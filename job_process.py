import os
from robot.api import logger
import subprocess
import codecs
from queue import Empty,Queue
import threading
from robotide.lib.robot.utils import encoding
from robotide.controller.testexecutionresults import TestExecutionResults



#I/O intensive   ==> read/write string from a lot of data/files



class JobProcess(object):
    """ This class is job process for jenkins"""
    
    def __init__(self,skip_job_preprocess):
        self._results=TestExecutionResults()
        self._skip_job_preprocess=skip_job_preprocess
        self._job_name=None
        self._jenkins_project_name=None
        self._git_branch=None
        self.public_keyword_location='basic'
        self._case_param=None #read from CASE_PARAM.{} of key:value
        self._test_plan=None #read from TEST_PLAN.[] of (tb_name,feature_name,case_list_file,skip_preprocess)
        self._jenkins_server=None #get from ${SSH_CONNECTION}
        self._shell_server=None #get from ${SSH_CONNECTION}
        self._job_owner=None #job owner or job submitter
        self._image_name=None #get from ${IMAGE_NAME}
        self._jenkins_url=None #read from JENKINS_URL
        self._web_base=None #http://xx/jenkins/${job_name}
        self._jenkins_job_path=None #/home/USER/workspace/JOB_NAME
        self._grouped_test_plan=None # a dict of {tb_name:[{feature_name,case_list,skip_preprocess},{}]
        self._tb_list=None
        #self._feature_name=None
        #
        self._case_list_file=None #get from ${TEST_PLAN}
        #self._tb_name=None #get from ${TEST_PLAN}   public/topo/tb_name.py
        self._queue=Queue()

    def init_env(self):
        #create directory /Temp/USER/JOBNAME_BuildID
        logger.info('Initial environment')
        print('Initial environment')
        self._job_owner=os.environ.get('USER')
        self._log_base=self._get_log_base_path()
        self._create_log_directory(self._log_base)
        #create command_list_file to store robot commands ==> execute in _write_command_file
        self.command_list_file=os.path.join(self._log_base,'command_list.txt')
        
        #self-defined param preprocess
        txt_case_param=os.environ.get('CASE_PARAM')
        if txt_case_param==None:
            logger.info('NO CASE_PARAM, upgrade cpe will NOT handle')
        self._case_param=self._txt_parse_to_dict(txt_case_param) #return case_param={'IMAGE':'http://image_url'}
        if self._case_param['IMAGE']:
            self._image_name=self._case_param['IMAGE']
            logger.info("IMAGE ==> %s" % self._case_param['IMAGE'])

        txt_test_plan=os.environ.get('TEST_PLAN')
        if txt_test_plan==None:
            logger.info('NO TEST PLAN found, please check again')
        self._test_plan=self._get_test_plan_list(txt_test_plan) #return test_plan=[{'tb':'tb_1.py','feature':'xxx','argfile':'/xx/xxx.txt'},{}]
        print('self._test_plan ==> %s'%self._test_plan)
        
        self._jenkins_job_path=os.path.join('/home',self._job_owner,'workspace',self._job_name) #/home/USER/workspace/JOB_NAME
        self._feature_dir=self._jenkins_job_path+'/features'
        logger.info("current user ==> %s" % self._job_owner)
        logger.info("Jenkins workspace ==> %s" % self._jenkins_job_path)
        

        
    def check_test_plan(self):
        pass


    def run_test_plan(self):
        self._write_command_file()
        thread_num=8
        for i in range(thread_num):
            t=threading.Thread(target=self._run_command,args=(i,self._queue,))
            t.setDaemon(True)
            t.start()
        with codecs.open(self.command_list_file,'r') as f:
            for command in f:
                self._queue.put(command)
        print('multi-thread run robot command start')
        self._queue.join()



    def save_snapshot(self):
        env_file_path=os.path.join(self._log_base,'env.log')
        cmd = 'env > %s' % env_file_path #save the env info to log_base/env.log
        logger.info('saving env snapshot to %s' % env_file_path)
        status,output=subprocess.getstatusoutput(cmd)
        if status:
            logger.warn('status ==> %s' % status)
            logger.warn('output ==> %s' % output)
            
        cmd_pip='pip list --format=columns >> %s' % env_file_path
        logger.info('saving pip list info to %s' % env_file_path)
        p_status,p_opt=subprocess.getstatusoutput(cmd_pip)
        if p_status:
            logger.warn('status ==> %s' % p_status)
            logger.warn('output ==> %s' % p_opt)

        
    def end_process(self):
        pass

    def _get_test_plan_list(self,txt_test_plan):
        """return test plan as a list which contains test_plan_dictionary
        such as [{'tb':'tb1.py','feature':'AP_VLAN','argfile':'/testplan/apvalan_case_for_dit.txt'}]
        """
        test_plan_list=[]
        lines=txt_test_plan.splitlines() #['tb1,feature,file','']
        for line in lines:
            tb,feature,argfile=line.split(',')
            dict={}
            dict['tb']=tb.strip()+'.py'
            dict['feature']=feature.strip()
            dict['argfile']=argfile.strip()
            test_plan_list.append(dict)
        print('test_plan_list: %s'%test_plan_list)
        return test_plan_list


    
    def _txt_parse_to_dict(self,txt):
        items={}

        if txt==None:
            return items
        lines= txt.splitlines()
        for line in lines:
            if line.strip()=='' or line.strip().startswith('#'):
                continue
            idx=line.index('=') #except the first '=',the other '=' belong to var_value
            key=line[:idx].strip()
            value=line[idx+1:].strip()
            items[key]=value
        
        return items


    def _get_log_base_path(self):
        #initial job log directory path
        self._job_name=os.environ.get('JOB_NAME') #sdwan-job-process
        jenkins_build_number=os.environ.get('BUILD_NUMBER')
        top_log_dir='/Temp'
        job_dir='{}_{}'.format(self._job_name,jenkins_build_number)
        log_base=os.path.join(top_log_dir,self._job_owner,job_dir)
        logger.info('JOB LOG DIRECTORY ==> %s' % log_base)
        #return log_base='/Temp/USER/JOBNAME_BUILDNUMBER'
        return log_base

    def _create_log_directory(self,log_base):
        """ Create a log directory """
        os.mkdir(log_base)


    def _create_command(self,suite_source_dir,case_list_file,tb_name,feature_name):
        """Return the command used to run the test"""

        command_as_list = ["robot"]
        argfile=os.path.join(self._feature_dir,case_list_file)
        variables=os.path.join(self._jenkins_job_path,'public/topo',tb_name)
        self._outputdir=os.path.join(self._log_base,feature_name)
        command_as_list.extend(["--argumentfile",argfile])
        command_as_list.extend(["-V",variables])
        command_as_list.extend(["--outputdir",self._outputdir])
        #command_as_list.extend(["--listener",MyListenerClass])
        command_as_list.append(suite_source_dir)
        print("command_as_list ==> %s" % command_as_list)

        command=" ".join(command_as_list)
        logger.info('run command ==> %s' % command)
        print('run command ==> %s'% command)
        return command

    def _write_command_file(self):

        command_list=[]
        for test in self._test_plan:
            try:
                tb_name=test['tb']
                feature_name=test['feature']
                case_list_file=test['argfile']
                #suite_source_dir=self._feature_dir                
                command=self._create_command(suite_source_dir=self._feature_dir,
                                            feature_name=feature_name,
                                            tb_name=tb_name,
                                            case_list_file=case_list_file)
                command_list.append(command)
                
            except Exception as e:
                logger.warn(e)
                print(e)
        #write command list file
        with codecs.open(self.command_list_file,'w',encoding='utf-8') as f:
            f.write("\n".join(command_list))

    

    def _run_command(self,thread_index,queue):
        while True:
            command=queue.get()
            print('thread %s run robot command %s' % (thread_index,command))
            if Empty:
                pass
            subprocess_args=dict(bufsize=0,
                                stdout=open('/home/jenkins/sdwan_jenkins/stdout.txt','a'),
                                stderr=subprocess.STDOUT)
            subprocess_args['preexec_fn']=os.setsid
            subprocess_args['shell']=True
            returncode=subprocess.call(command,**subprocess_args)
            if returncode:
                print('execute shell command fail!')
            queue.task_done()
        



        
        






if __name__=="__main__":
    run=JobProcess(skip_job_preprocess=True)