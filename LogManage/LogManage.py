from robot.api import logger
import re



class LogManage(object):

    def get_segment(self,ip_addr,mask):
        """Get network IP and subnet mask according to the given ip address and mask.
        
        :param str ip_addr: the ip address which is already known.
        :param str mask: the mask of the ip_addr.
        :return segment,port: return the segment ,port as a tuple.

        example:
            | ${ip_addr} | set variable | 192.168.3.1 |
            | ${mask} | set variable | 255.255.255.0 |
            | ${segment_port} | get segment | ${ip_addr} | ${mask} |
        """
        self.segment=[]
        self.port=0

        try:
            ip_addr=ip_addr.split('.')
            mask=mask.split('.')
            for i in range(4):
                seg_ip=int(ip_addr[i])&int(mask[i])
                self.segment.append(str(seg_ip))
            self.segment='.'.join(self.segment)
            for item in mask:
                num=bin(int(item)).count('1')
                self.port+=num
            self.port=str(self.port)
        except Exception as e:
            logger.warn(e)
        return self.segment,self.port

    def _pre_process_msg(self,msg_input):
        if msg_input=="":
            return "msg input error, should be string,not null"
        else:
            msg=msg_input.strip()
            return msg

    def _pre_process_talbe_to_dict(self,table,header_index=1):
        """change str table to a dictionary list such as:
        [{'header':'line_1'},...,{'header':'line_n'}]
        :param int offset: is the index of the table's header
        """
        table=table.strip().split('\n')
        tmp=[]
        for line in table:
            line=re.sub(r'\s+',' ',line)
            line=line.split(' ')
            tmp.append(line)
        
        tmp_list=[]
        for line in tmp:
            if len(line)==len(tmp[header_index]):
                tmp_list.append(line)
        
        table_list=[]
        for row in range(len(tmp_list)-1):
            table_dict={}
            line=tmp_list[row+1]
            for colum in range(len(tmp_list[0])):
                table_dict[tmp_list[0][colum]]=line[colum]
            table_list.append(table_dict)
        return table_list


            
    def get_info_from_table(self,table,arg_1,arg_2,target_info,offset=2):
        """Get target information from a table with two arguments which is already known.
        
        What is a table?

        A table contains a header and rows.
        when you execute 'route' on cpe, it supposes to get a table as below:

        | Kernel IP routing table |
        | Destination  |   Gateway     |   Genmask       |  Flags | Metric | Ref  |  Use | Iface |
        | default     |    10.201.0.1   |   0.0.0.0     |    UG  |  1   |   0    |    0 | eth1 |
        | 10.201.0.0  |    *     |          255.255.255.0  | U  |   1   |   0   |     0 | eth1 |
        | 100.64.0.0   |   *     |          255.255.0.0   |  U  |   1  |    0  |      0 | vti76 |
        | 100.64.0.0    |  *         |      255.255.0.0    | U    | 2     | 0      |  0 | vti45 |

        In this case if you want to get Metric according to the given Destination and Interface,
        you can take the example::

        | ${Metric} | get info by given arguments | ${table} | Destination=10.201.0.0 | Iface=eth1 | Metric |

        :param str table: the table from which get info

        :param str arg_1: the  given argument with the header and the value of header

        :param str arg_2: a different argument like 'diff_header=value' which is aim to locate the one and only target_info

        :param str target_info: the header of target info such as 'Metric'

        :param int offset: the row index of the header, default is 2, which means the second line is the header of the table

        """
        #input param check, if param is null, raise assertionerro and end the execution
        if table=='':
            logger.warn('table input error: should be string, not null')
            raise AssertionError('table input error: should be string, not null')
        if arg_1=='' or arg_2=='':
            logger.warn('argument error: should be string, not null')
            raise AssertionError('argument error: should be string, not null')
        if target_info=='':
            logger.warn('target_info error: should be string, not null')
            raise AssertionError('target_info error: should be string, not null')
        #input param process
        arg_1,arg_2=arg_1.strip(),arg_2.strip()
        target_info=target_info.strip()
        
        try:
            offset=int(offset)-1
            table_list=self._pre_process_talbe_to_dict(table,header_index=offset)
            key_1,value_1=arg_1.split('=')
            key_2,value_2=arg_2.split('=')
            for line in table_list:
                if line[key_1]==value_1 and line[key_2]==value_2:
                    target_value=line[target_info]
        except Exception as e:
            logger.warn(e)
        
        return target_value

    def get_line_from_table(self,table,base_phase,offset=2):
        """Get line(s) with a dictionary type from a table accroding to the given parameter.

        What is a table?

        A table contains a header and rows.
        when you execute 'route' on cpe, it supposes to get a table as below:

        | Kernel IP routing table |
        | Destination  |   Gateway     |   Genmask       |  Flags | Metric | Ref  |  Use | Iface |
        | default     |    10.201.0.1   |   0.0.0.0     |    UG  |  1   |   0    |    0 | eth1 |
        | 10.201.0.0  |    *     |          255.255.255.0  | U  |   1   |   0   |     0 | eth1 |
        | 100.64.0.0   |   *     |          255.255.0.0   |  U  |   1  |    0  |      0 | vti76 |
        | 100.64.0.0    |  *         |      255.255.0.0    | U    | 2     | 0      |  0 | vti45 |

        In this case if you want to get the line of which the Destionation is '10.201.0.0',
        you can take the example::
        | ${target_line} | get line from table | ${table} | Destination=10.201.0.0 |

        :param str table: the table from which get line(s)

        :parm str base_phase: the base_phase given by user accroding to which to locate the line
         
        :return dict: retrun line(s) with the dictionary type such as: 
        
        {'Destination': '10.201.0.0', 'Gateway': '*', 'Genmask': '255.255.255.0', 'Flags': 'U', 'Metric': '1', 'Ref': '0', 'Use': '0', 'Iface': 'eth1'}

        or: [{'Destination': '192.168.1.0', 'Gateway': '*', 'Genmask': '255.255.255.0', 'Flags': 'U', 'Metric': '1', 'Ref': '0', 'Use': '0', 'Iface': 'vti76'}, {'Destination': '192.168.1.0', 'Gateway': '*', 'Genmask': '255.255.255.0', 'Flags': 'U', 'Metric': '2', 'Ref': '0', 'Use': '0', 'Iface': 'vti45'}]
        
        :param int offset: the row index of the header, default is 2, which means the second line is the header of the table

        """
        #input param check, if param is null, raise assertionerro and end the execution
        if table=='':
            logger.warn('table input error: should be string, not null')
            raise AssertionError('table input error: should be string, not null')
        if base_phase=='':
            logger.warn('base_phase input error: should be string, not null')
            raise AssertionError('base_phase input error: should be string, not null')
        #input param process
        offset=int(offset)-1
        base_phase=base_phase.strip()
        target_line=[]
        try:
            table_list=self._pre_process_talbe_to_dict(table,header_index=offset)
            key,value=base_phase.split('=')
            for line in table_list:
                if line[key]==value:
                    target_line.append(line)
            if len(target_line)==1:
                target_line=target_line[0]
        except Exception as e:
            logger.warn(e)

        return target_line


        




        
        






        
import paramiko


if __name__=="__main__":
    test=LogManage()
    
    client=paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname='10.201.0.217',username='root',password='sdwan')
    stdin,stdout,stderr=client.exec_command('route')
    table=stdout.read().decode('utf-8')
    #Iface=test.get_info_from_table(table,'Destination=10.201.0.0','Metric=1','Iface')
    #print(Iface)
    line=test.get_line_from_table(table,'Destination=10.201.0.0')
    print(line)
    
