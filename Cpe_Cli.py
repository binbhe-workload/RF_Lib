import os
import re,time
import paramiko
import subprocess
from robot.api import logger
from SSHLibrary.library import SSHLibrary

class Cpe_Cli(SSHLibrary):
    
    def _get_latest_image(self,image_type):
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname='172.31.25.77',username='autobuild',password='linkwan123456')
            stdout = client.exec_command('ls -t /home/developers/images/%s' % image_type)        
            output = stdout[1].read().decode('utf-8')
            all_image_dir = output.split('\n')
            client.close()

            latest_image = os.path.split(all_image_dir[0])[1]
            logger.info('latest_image is: %s' % latest_image)
        
        except Exception as e:
            latest_image='no image found!'
            logger.warn(e)
        return latest_image


    def upgrade_image(self,image_name,clean_conf='false'):
        """Upgrade image for CPE via using command 'sysupgrade (-n) url'
        if you want to upgrade CPE with the latest version of image for example:
            | open connection | ${cpe_ip} |
            | login | ${cpe_username} | ${cpe_password} | 
            | upgrade image | E201 |

        if you want to use the specific version of image, replace the part of upgrade image to:
            | upgrade image | E201-vx.x.x.bin |

        if you want to clean the config after upgrade CPE, append argument clean_conf=true as below:
            | upgrade image | clean_conf=true |
            or:
            | upgrade image | E201-vx.x.x.bin | clean_conf=true |
        """
        if image_name == 'E201' or image_name == 'V501':
            image = self._get_latest_image(image_name)
            if image=='no image found!':
                logger.warn('no image found,please check whether image exists in file path http://172.31.25.77:8880/images')
                raise AssertionError('no image found')
        elif image_name.endswith('bin') or image_name.endswith('img'):
            image = image_name    

        url='http://172.31.25.77:8880/images/'+image
        logger.info('image_url is: %s' % url)

        self._upgrade_image(url,clean_conf)
        

    def _upgrade_image(self,url,clean_conf):

        if clean_conf == 'false':
            cmd = 'sysupgrade ' + url
        elif clean_conf.lower() == 'true':
            cmd = 'sysupgrade -n ' + url
        logger.info('upgrade CPE via command: %s' % cmd,also_console=True)
        try:
            current_host = self.current.config.host
            output = self.current.execute_command(cmd)
            upgrade_result = output[1]
            logger.info(upgrade_result,also_console=True)
            logger.info(output[0],also_console=True)
            if not re.search(r'Download completed',upgrade_result):
                logger.warn('Download image from %s failed!' % url)
            if re.search(r'Closing all shell sessions',output[0]):
                time.sleep(15)
                cpe_connection = self._ping_device(current_host)
                if cpe_connection == 1:
                    logger.info('ping cpe success,prepare to check current image version of cpe')
                    #self.open_connection(current_host)
                    #open connection but not login due to lack of usr/pwd
                if cpe_connection == 0:
                    logger.warn('ping cpe timeout,please check cpe status manually')
        except Exception as e:
            logger.error(e)
    



    def _ping_device(self,host,total=30):
        logger.info('ping device with host ip: %s' % host)
        ping_cmd='ping -c5 -W50 %s' % host 
        #logger.info(ping_cmd)
        count=1
        ping_pass=0
        while count<=total and ping_pass==0:
            ping_result=subprocess.getoutput(ping_cmd)
            if re.search(r'5 packets transmitted, 5 packets received',ping_result):
                ping_pass=1
            else:
                count+=1
                time.sleep(5)
        if count>total and ping_pass==0:
            logger.warn('ping timeout, could not connect to %s' % host)
        return ping_pass

    def get_image_version(self):
        """Return version info of cpe as a dictionary like:
        {'PLATFORM': 'CPE201', 'COMPILER': 'autobuild@ubuntu', 'OSVERSION': 'v3.0.0_beta1', 'BUILD_COOKIE': '19-g4e3beea'}
        """
        output=self.current.execute_command('cat /netbank/linkos_version')
        logger.info(output[0])
        
        try:
            version=output[0]
            version=version.strip().split('\n')
            logger.info('version_list is %s ' % version)
            dict={}
            for line in version[:-1]:
                key,value=line.split(':')
                key,value=key.strip(),value.strip()
                dict[key]=value
            #current_version=dict['PLATFORM']+'-image-'+dict['OSVERSION']+'-'+dict['BUILD_COOKIE']
            #logger.info('current image version is: %s' % current_version)
        except Exception as e:
            logger.warn(e)
        return dict


    
    def _check_image_version(self):
        """Check image version after upgrade cpe"""
        pass



    def clean_image(self):
        """Keep the lastest 30 images while clean the workspace periodically."""
        try:
            all_image=self.current.execute_command('ls -t /home/developers/images')
            all_image=all_image[0]
            image_list=all_image.strip().split('\n')
            if len(image_list)>30:
                #logger.info(image_list[30:])
                for image in image_list[30:]:
                    cmd='rm -rf /home/developers/images/'+image
                    logger.info(cmd)
                    self.current.execute_command(cmd)
        except Exception as e:
            logger.warn(e)

    
    def get_rpi_interface_ip(self,interface="eth0"):
        """Get the specific ip of Raspberry Pi 

        :param str interface: default is 'eth0', dynamic ip which is allocated by CPE

        :returns str: IP address of the interface
        
        example::
        | ${eth0_ip} | get rpi interface ip |
        | ${eth1_ip} | get rpi interface ip | eth1 |
        """
        output = self.current.execute_command('ifconfig %s' % interface)
        inet = re.search(r'inet \d+.\d+.\d+.\d+',output[0])
        #print(output[0],type(output[0]))
        if inet:
            return inet.group().split(' ')[1]
        else:
            logger.warn('Can not get ip address for interface %s' % interface)


    def reset_rpi_interface_ip(self,interface='eth0'):
        """Reset the specific interface ip of Respberry Pi

        :param str interface: default is 'eth0',dynamic ip allocated by CPE

        :returns str: IP address of the interface after reset interface
        
        example::
        | ${eth0_ip} | reset rpi interface ip |
        """
        self.current.execute_command('ifconfig %s down' % interface)
        output = self.current.execute_command('ifconfig %s' % interface)
        inet = re.search(r'inet \d+.\d+.\d+.\d+',output[0])
        for index in range(10):
            time.sleep(1)
            if inet:
                logger.warn('<DOWN LOOP %s> Fail to down interface %s!' % (index,interface))
                continue
            else:
                logger.info('<DOWN LOOP %s> interface %s is down, reset procedure is on going' % (index,interface))
                break

        self.current.execute_command('ifconfig %s up' % interface)
        if not inet:
            for i in range(10):
                time.sleep(1)
                output = self.current.execute_command('ifconfig %s' % interface)
                inet = re.search(r'inet \d+.\d+.\d+.\d+',output[0])
                if inet:
                    logger.info('<UP LOOP %s> interface %s is up' % (i,interface))
                    ip = inet.group().split(' ')[1]
                    logger.info('Get interface ip >> %s' % ip)
                    br_lan = ip.split('.')[:-1]
                    br_lan.append('1')
                    br_lan = '.'.join(br_lan)
                    res = self.current.execute_command('ping -c5 -W50 %s' % br_lan)
                    if re.search(r'5 packets transmitted, 5 received',res[0]):
                        logger.info('Ping br-lan %s ok' % br_lan)
                        return ip
                    else:
                        logger.warn('Ping br-lan %s fail, re-process reset %s' % (br_lan,interface))
                        self.reset_rpi_interface_ip(interface)
                    break
                else:
                    logger.warn('<UP LOOP %s> interface %s reset fail!' % (i,interface))
                    continue
            