import os
import logger
import subprocess
import codecs
import threading
from queue import Queue,Empty





class JobProcess(object):
    """This class is the main job process of Jenkins triggered RF autotests"""

    def __init__(self,skip_job_preprocess):
        self._skip_job_preprocess=skip_job_preprocess  #bool define if skip the job preprocess
        self._job_owner=None   #get from env ${USER}
        self._job_name=None    #get from env ${JOB_NAME}
        self._log_base=None    #top log directory of current job
        self._case_param=None  #dict type of case_param get from env ${CASE_PARAM}
        self._image_name=None  #get from self._case_param
        self._test_plan={}     #grouped test plan get from env ${TEST_PLAN}
        self._tb_list=None     #generate from self._test_plan
        self._jenkins_job_path=None  #generate from ${USER},${JOB_NAME}
        self._featrue_dir=None       #generate from self._jenkins_job_path
        self._testplan_dir=None      #generate form self._feature_dir
        self._topo_dir=None          #generate from self._jenkins_job_path
        self._preprocess_script_dir=None  #generate from self._jenkins_job_path
        self._feature_path_list=[]        #get from self._create_list_of_feature_and_argfile()
        self._argfile_path_list=[]   #get from self._create_list_of_feature_and_argfile()
        self._queue = Queue()


    


    
    def init_env(self):
        """ initial test environments"""

        logger.info('Initial test environments')

        #create log_base_dir >> /Temp/${USER}/${JOBNAME}_${BuildID}
        self._get_log_base()
        self._create_log_directory(self._log_base)

        #parse CASE_PARAM get from env
        txt_case_param = os.environ.get('CASE_PARAM')
        if txt_case_param == None:
            logger.warn('NO CASE PARAM, upgrade CPE will NOT handle!')
        self._case_param = self._txt_parse_to_dict(txt_case_param) #return case_param={'IMAGE':'http://image_url'} or {}
        if self._case_param['IMAGE']:
            self._image_name = self._case_param['IMAGE']
            logger.info("IMAGE >> %s" % self._image_name)

        
        #parse test_plan get from env
        txt_test_plan = os.environ.get('TEST_PLAN')
        if txt_test_plan == None:
            logger.critical('NO TEST PLAN found, will end job process!')
            raise AssertionError('NO TEST PLAN found!')
        else:
            self._group_test_plan(txt_test_plan) 
            #return {'tb_index':[{'feature':'AP_VLAN','argfile':'/testplan/apvalan_case_for_dit.txt'},{}],}

        #parse autocase scripts local workspace path which gitlab fetch branch to
        self._jenkins_job_path = os.path.join('/home',self._job_owner,'workspace',self._job_name)  #/home/USER/workspace/JOB_NAME
        logger.info('current jenkins job workspace >> %s' % self._jenkins_job_path)
        self._featrue_dir = os.path.join(self._jenkins_job_path,'features')
        logger.info('feature scripts directory >> %s' % self._featrue_dir)
        self._testplan_dir = os.path.join(self._featrue_dir,'testplan')
        logger.info('testplan directory >> %s' % self._testplan_dir)
        self._topo_dir = os.path.join(self._jenkins_job_path,'public/topo')
        logger.info('public topo directory >> %s' % self._topo_dir )
        self._preprocess_script_dir = os.path.join(self._jenkins_job_path,'public/basic')
        logger.info('preprocess script directory >> %s' % self._preprocess_script_dir)


    
    def check_test_plan(self):
        """ Check test plan and re-generate test plan if error exist"""

        error_num = 0
        self._create_list_of_feature_and_argfile_path()
        logger.info('Start test plan check')
        #check if tb_index.py existed
        self._tb_list = list(self._test_plan.keys())
        for tb_name in self._tb_list:
            tb_topology_path = os.path.join(self._topo_dir,'{}.py'.format(tb_name))
            if not os.path.exists(tb_topology_path):
                logger.warn('TB topology file %s.py Not found!' % tb_name)
                error_num += 1

        #check if feature directory existed
        for feature_path in self._feature_path_list:
            if os.path.exists(feature_path) or os.path.exists(feature_path+'.robot'):
                pass
            else:
                logger.warn('Feature %s or %s.robot Not found!' % feature_path)
                error_num += 1

        #check if argfile existed
        for argfile in self._argfile_path_list:
            if not os.path.exists(argfile):
                logger.warn('argfile %s Not found!' % argfile)
                error_num += 1

        #check test suites in argfiles if existed in sub_feature directory or sub_feature.robot
        #check if IMAGE existed in IMAGE SERVER
        
        if error_num > 0 :
            logger.warn('Test plan check failed!')
            raise AssertionError('Test plan check failed! Found %s erros!' % error_num)
        else:
            logger.info('Test plan check success!')

        
    def run_test_plan(self):
        """Main testcase run method"""

        #check if CPE upgrade is choosed
        if self._image_name:
            self._upgrade_cpe()

        #check if --skip-job-preprocess is specified by tester
        if self._skip_job_preprocess:
            logger.info('Detected option --skip-job-preprocess, Skip job preprocess!')
        if not self._skip_job_preprocess:
            self._job_preprocess()

        #create tb_log_base to save each tb cases logs
        for tb in self._tb_list:
            tb_log_dir=os.path.join(self._log_base,tb)
            self._create_log_directory(tb_log_dir)

        #write command file for each tb
        self._write_command_file()

        #start multi-threading tb cases running procedure
        thread_num=8
        for i in range(thread_num):
            t=threading.Thread(target=self._run_command,args=(i,self._queue,))
            t.setDaemon(True)
            t.start()
        for tb in self._tb_list:
            self._queue.put(tb)
        logger.info('Mulit tb sites run robot cases start!')
        self._queue.join()
        

    
    def save_snapshot(self):
        """Save snapshot for testinf related env infromation"""

        env_file_path = os.path.join(self._log_base,'env.log')
        cmd = 'env > %s' % env_file_path
        logger.info('Saving env log to %s' % env_file_path)
        status,output = subprocess.getstatusoutput(cmd)
        if status:
            logger.warn('Save env log failed!')
            logger.warn('Detail output >> \n %s' % output)

        cmd_pip = 'pip list --format=columns >> %s' % env_file_path
        logger.info('Saving pip list log to %s' % env_file_path)
        p_status,p_output = subprocess.getstatusoutput(cmd_pip)
        if p_status:
            logger.warn('Save pip list log failed!')
            logger.warn('Detail output >> \n %s' % p_output)
        




    def _get_log_base(self):

        self._job_owner = os.environ.get('USER')
        logger.info('Get job owner >> %s' % self._job_owner)
        self._job_name = os.environ.get('JOB_NAME')
        build_number = os.environ.get('BUILD_NUMBER')
        job_dir = '{}_{}'.format(self._job_name,build_number)
        self._log_base = os.path.join('/Temp',self._job_owner,job_dir)
        logger.info('Top Log Directory >> %s' % self._log_base)

    
    def _create_log_directory(self,log_base_dir):
        
        os.mkdir(log_base_dir)
        logger.info('Create directory >> %s' % log_base_dir)

    
    def _txt_parse_to_dict(self,txt):
        """ parse string to a dictionary"""

        item = {}
        if txt:
            lines = txt.splitlines()
            for line in lines:
                if line.strip() == '' or line.strip().startswith('#'):
                    continue
                idx = line.index('=')
                key = line[:idx].strip()   #except the first '=',the other '=' belong to var_value
                value = line[idx+1:].strip()
                item[key] = value
        return item

    
    def _group_test_plan(self,txt_test_plan):
        """return a dict of {'tb_list':[test_plan_dic]}
        such as {'tb_index':[{'feature':'AP_VLAN','argfile':'/testplan/apvalan_case_for_dit.txt'},{}],}"""

        lines = txt_test_plan.splitlines()   #['tb1,feature,file','']
        for line in lines:
            tb,feature,argfile = line.split(',')
            tb = tb.strip()
            if tb not in self._test_plan:
                self._test_plan[tb] = []
            tb_case = {}
            tb_case['feature'] = feature.strip()
            tb_case['argfile'] = argfile.strip()
            self._test_plan[tb].append(tb_case)

    
    
    def _create_list_of_feature_and_argfile_path(self):
        """This function is merged by 
        self._get_testplan_feature_list and
        self._get_argfile_path_list """

        for tb_name in self._test_plan:
            case_list = self._test_plan[tb_name]
            for single_case in case_list:
                feature = single_case['feature']
                argfile = single_case['argfile']
                feature_path=os.path.join(self._featrue_dir,feature)
                if feature_path not in self._feature_path_list:
                    self._feature_path_list.append(feature_path)
                argfile_path = os.path.join(self._featrue_dir,feature,argfile)
                if argfile_path not in self._argfile_path_list:
                    self._argfile_path_list.append(argfile_path)


    def _job_preprocess(self):
        """Process this method if self._skip_job_preprocess==False"""
        pass


    def _upgrade_cpe(self):
        """Process CPE upgrade procedure 
        if IMAGE is detected in ${CASE_PARAM}"""
        pass

    
    def _write_command_file(self):
        """ wirte command list file for each tb site"""

        for tb in self._tb_list:
            tb_path=os.path.join(self._topo_dir,'{}.py'.format(tb))
            case_list = self._test_plan[tb]
            tb_command_list=[]
            tb_log_dir=os.path.join(self._log_base,tb)
            for single_case in case_list:
                argfile = single_case['argfile']
                feature = single_case['feature']
                # if argfile.startswith('/testplan') or argfile.startswith('testplan'):
                #     argumentfile = os.path.join(self._featrue_dir,argfile)
                # else:
                #     argumentfile = os.path.join(self._testplan_dir,argfile)
                #change argumentfile directory to feature folder put with FeatureSuite.robot
                argumentfile = os.path.join(self._featrue_dir,feature,argfile)
                output_dir = os.path.join(tb_log_dir,feature)
                feature_dir = os.path.join(self._featrue_dir,feature)

                command = self._create_command(argumentfile,tb_path,output_dir,feature_dir)
                if command not in tb_command_list:
                    tb_command_list.append(command)
            #logger.info('tb_command_list >> %s' % tb_command_list)
            tb_command_path = os.path.join(tb_log_dir,'{}_command.txt'.format(tb))
            with codecs.open(tb_command_path,'w',encoding='utf-8') as f:
                f.write('\n'.join(tb_command_list))
            logger.info('{}_command.txt created in {}'.format(tb,tb_log_dir))

    
    def _create_command(self,argumentfile,tb_path,output_dir,feature_dir):
        """Return the robot command"""

        command_as_list = ["robot"]
        command_as_list.extend(['--argumentfile',argumentfile])
        command_as_list.extend(['-V',tb_path])
        command_as_list.extend(['--outputdir',output_dir])
        command_as_list.append(feature_dir)

        command =" ".join(command_as_list)
        #logger.info('Create command >> %s' % command)
        return command

    def _run_command(self,thread_index,queue):
        """Run method for threading run target"""

        while True:
            tb = queue.get()
            logger.info('Thread %s run %s cases' % (thread_index,tb))
            tb_log_dir = os.path.join(self._log_base,tb)
            tb_command_path = os.path.join(tb_log_dir,'{}_command.txt'.format(tb))
            tb_run_stdout = os.path.join(tb_log_dir,'{}_stdout.txt'.format(tb))
            with codecs.open(tb_command_path,'r') as f:
                for command in f:
                    resnum = subprocess.call(command,shell=True,
                                            stdout=open(tb_run_stdout,'a'),
                                            stderr=subprocess.STDOUT,
                                            preexec_fn=os.setsid)
                    if resnum:
                        logger.warn('Run command %s failed!' % command)
            queue.task_done()
            logger.info('%s test cases done!' % tb)






