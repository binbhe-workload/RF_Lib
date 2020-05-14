import os
import codecs
import logger
import argparse
from robot.parsing import TestData



def main(parser):
    args = parser.parse_args()
    source = args.source

    generate_argfile = Generate_argfile()
    try:
        generate_argfile.parse_testdata(source)
    except Exception as e:
        logger.warn(e)


Parser = argparse.ArgumentParser(description='Generate _full_cases_list.txt')

Parser.add_argument('--source',default='default',
                    help='Specific the feature source directory where _full_cases_list.txt generate from')



class Generate_argfile(object):
    """Implements writing of parsed test case files to a argfile"""
    def __init__(self):
        self._feature_dir = None   #get from os.envrion
        self._feature_list = []  #get from self._feature_dir
        self.user_source = None    #get from argparse given by user

    def _get_feature(self):
        try:
            job_owner = os.environ.get('USER')
            job_name = os.environ.get('JOB_NAME')
            self._feature_dir = os.path.join('/home',job_owner,'workspace',job_name,'features')
            #self._feature_dir = '/home/jenkins/workspace/sdwan-job-process/features'
            for feature in os.listdir(self._feature_dir):
                feature_source = os.path.join(self._feature_dir,feature)
                if os.path.isdir(feature_source):
                    self._feature_list.append(feature_source)

        except Exception as e:
            logger.warn(e)


    def _write_argfile(self,suite_dir):
        
        try:
            #Parse a suite_dir to a directory of suite/case_list pairs
            tmp = {}
            feature = TestData(source=suite_dir)
            for suite in feature.children:
                test = []
                if suite.testcase_table:
                    for case in suite.testcase_table:
                        test.append(case.name)
                    tmp[suite.name] = test
            
            #Write argfile for each feature floder
            argfile = os.path.join(suite_dir,'_full_cases_list.txt')
            with codecs.open(argfile,'w',encoding='utf-8') as f:
                for suite,test_list in tmp.items():
                    f.write('--suite\n%s\n--test\n' % suite)
                    f.write('\n--test\n'.join(test_list))
                    f.write('\n')
            logger.info('_full_cases_list.txt writed in %s' % suite_dir)
        except Exception as e:
            logger.warn(e)               
        

    def parse_testdata(self,source='default'):
        
        if source == 'default':
            self._get_feature()
            for suite_dir in self._feature_list:
                self._write_argfile(suite_dir)
        elif os.path.exists(source):
            self._write_argfile(source)
        else:
            logger.warn('Invalid source: %s' % source)



if __name__=="__main__":
    main(Parser)
