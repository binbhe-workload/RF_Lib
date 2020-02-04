import os
#import request
import subprocess
import json
import re
from robot.api import logger

#dic={"username":"admin","password":"sdwan123!@#"}
payload={}
payload["username"],payload["password"]=input().split()
data="'"+ json.dumps(payload) + "'"

url='http://admin.dev.linksdwan.com'
cmd='curl -H "Content-Type: application/json"  -X POST -d '+data+' -k %s/proxy/auth/login' % url

jsondata=[{'id': 424, 'remarksManager': None, 'remarksAgent': None, 'remarksTenant': None, 'status': '未分配代理商', 'type': 'E201', 'operatingSystem': None, 'bandwidth': None, 'gmtCreate': '2020-01-09T20:39:01Z', 'gmtModified': '2020-01-09T20:39:01Z', 'locked': None, 'key': None, 'channelId': None, 'regionId': None, 'projectId': None, 'tenantId': None, 'agentId': None, 'vpeId': None, 'masterPopId': None, 'slavePopId': None, 'masterState': None, 'slaveState': None, 'regionName': None, 'projectName': None, 'masterIsp': None, 'slaveIsp': None, 'popRx': None, 'popTx': None, 'internetTx': None, 'internetRx': None, 'masterPop': None, 'slavePop': None, 'masterVpe': None, 'standbyVpe': None, 'deviceConfigId': None, 'deviceConfigDraftId': None, 'tenantSmallDTO': None, 'agentSmallDTO': None, 'sn': 'E201201911191993', 'versionNumber': '1.3.9', 'equipmentName': 'E201201911191993', 'logisticsId': None, 'logisticsNumber': None}, {'id': 423, 'remarksManager': None, 'remarksAgent': None, 'remarksTenant': None, 'status': '未分配代理商', 'type': 'E201', 'operatingSystem': None, 'bandwidth': None, 'gmtCreate': '2020-01-09T20:39:01Z', 'gmtModified': '2020-01-09T20:39:01Z', 'locked': None, 'key': None, 'channelId': None, 'regionId': None, 'projectId': None, 'tenantId': None, 'agentId': None, 'vpeId': None, 'masterPopId': None, 'slavePopId': None, 'masterState': None, 'slaveState': None, 'regionName': None, 'projectName': None, 'masterIsp': None, 'slaveIsp': None, 'popRx': None, 'popTx': None, 'internetTx': None, 'internetRx': None, 'masterPop': None, 'slavePop': None, 'masterVpe': None, 'standbyVpe': None, 'deviceConfigId': None, 'deviceConfigDraftId': None, 'tenantSmallDTO': None, 'agentSmallDTO': None, 'sn': 'E201201911191994', 'versionNumber': '1.3.9', 'equipmentName': 'E201201911191994', 'logisticsId': None, 'logisticsNumber': None}, {'id': 338, 'remarksManager': None, 'remarksAgent': None, 'remarksTenant': None, 'status': '未分配代理商', 'type': 'E201', 'operatingSystem': None, 'bandwidth': 4, 'gmtCreate': '2020-01-03T01:21:03Z', 'gmtModified': '2020-01-03T16:06:35Z', 'locked': None, 'key': None, 'channelId': None, 'regionId': None, 'projectId': None, 'tenantId': None, 'agentId': None, 'vpeId': None, 'masterPopId': None, 'slavePopId': None, 'masterState': None, 'slaveState': None, 'regionName': None, 'projectName': None, 'masterIsp': None, 'slaveIsp': None, 'popRx': None, 'popTx': None, 'internetTx': None, 'internetRx': None, 'masterPop': None, 'slavePop': None, 'masterVpe': None, 'standbyVpe': None, 'deviceConfigId': None, 'deviceConfigDraftId': None, 'tenantSmallDTO': None, 'agentSmallDTO': None, 'sn': 'E201201922294092', 'versionNumber': '1.3.9', 'equipmentName': 'E201201922294092', 'logisticsId': None, 'logisticsNumber': None}, {'id': 337, 'remarksManager': None, 'remarksAgent': None, 'remarksTenant': None, 'status': '未分配代理商', 'type': 'E201', 'operatingSystem': None, 'bandwidth': 4, 'gmtCreate': '2020-01-03T01:21:03Z', 'gmtModified': '2020-01-03T16:06:47Z', 'locked': None, 'key': None, 'channelId': None, 'regionId': None, 'projectId': None, 'tenantId': None, 'agentId': None, 'vpeId': None, 'masterPopId': None, 'slavePopId': None, 'masterState': None, 'slaveState': None, 'regionName': None, 'projectName': None, 'masterIsp': None, 'slaveIsp': None, 'popRx': None, 'popTx': None, 'internetTx': None, 'internetRx': None, 'masterPop': None, 'slavePop': None, 'masterVpe': None, 'standbyVpe': None, 'deviceConfigId': None, 'deviceConfigDraftId': None, 'tenantSmallDTO': None, 'agentSmallDTO': None, 'sn': 'E201201922294091', 'versionNumber': '1.3.9', 'equipmentName': 'E201201922294091', 'logisticsId': None, 'logisticsNumber': None}]

#def get_attribute_x_value_by_y(jsondata,x,y):
def get_id_by_other_message(jsondata,msg,msg_value):

        '''Return the value of id when we know the value of another message in the dictionary /json list.
        
        :param jsondata: the JSON string or dict or list,which is iterable
        
        :param str msg: the message which is already known.
        
        :param str msg_value: the value of message.
        
        :returns: value(s) of x. If only one value got, return it, or else return
            matched values list.
            
        Note::
        
            the default type of message and value is string.
        
        Example::
        
        
        | ${device_id}=	| Get Attribute X Value By Y | ${json} | equipmentName | E201201922294091 |
        
        '''
        if not jsondata:
                print("jsondata is null,please check the response data")
        else:
                try:
                        if isinstance(jsondata,list):
                                for item in jsondata:
                                        #print(type(item))
                                        if isinstance(item,dict):
                                                if item[msg]==msg_value:
                                                        id=item['id']
                                        else:
                                                logger.info(item)
                                                logger.info('is not a dictionary')
                        return id
                except Exception as e:
                        print(e)
                                
                

print(get_id_by_other_message(jsondata,'equipmentName','E201201922294091'))







