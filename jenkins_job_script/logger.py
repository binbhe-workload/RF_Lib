import logging

#create logger
logger = logging.getLogger('JenkinsJobProcess')
logger.setLevel(logging.INFO)

#create console handler and set level to info
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

#create formatter
formatter = logging.Formatter('%(asctime)s %(name)s <%(levelname)s> %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

#add formatter to handler
handler.setFormatter(formatter)

#add handler to logger
logger.addHandler(handler)


def write(msg,level="INFO"):
    #create logger
    #logger=logging.getLogger('JenkinsJobProcess')
    level={'DEBUG':logging.DEBUG,
           'INFO':logging.INFO,
           'WARN':logging.WARN,
           'CRITICAL':logging.CRITICAL}[level]

    logger.log(level,msg)


def debug(msg):
    write(msg,'DEBUG')

def info(msg):
    write(msg,'INFO')

def warn(msg):
    write(msg,'WARN')

def critical(msg):
    write(msg,'CRITICAL')


        
