import datetime
import os

base = '/home/sdwan/Test/logs'
output_dir = os.path.join(base,datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.mkdir(output_dir)
