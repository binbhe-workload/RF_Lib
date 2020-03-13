import os
import argparse
from robot.api import logger
from job_process import JobProcess

def main(parser):
    args = parser.parse_args()
    skip_job_preprocess=args.skip_job_preprocess
    
    job_process=JobProcess(skip_job_preprocess)

    try:
        job_process.init_env()
        job_process.check_test_plan()
        job_process.run_test_plan()
        #job_process.save_snapshot()

    except Exception as e:
        logger.warn(e)
        print('sdwan_jenkins_main alarm ==> %s' % e)

Parser = argparse.ArgumentParser(description='AAF Main Program')

Parser.add_argument('--skip-job-preprocess',
                    help='Do not execute AAF public job pre-process',
                    action='store_true')


if __name__=="__main__":
    main(Parser)