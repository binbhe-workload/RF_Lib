import os
import re
import json
import requests
#import warnings
from requests_toolbelt import MultipartEncoder
import subprocess
#import collections

from robot.api import logger
import  time
import random
import string


class API_Test_Lib(object):

    
    def __init__(self):
        #warnings.filterwarnings("ignore")
        self._user = None
        self._password = None
        self.cookie = None
        self.csrf = None
        self._headers = None
        self._headers_fullpath = None      #os.path.expanduser('~') + '/headers'
        self.base_url = ''
        self.current_URL = ''
        self._session = None     #provides cookie persistence, connection-pooling, and configuration
        self.query =''
        self.timeout = 150       # Default time for all the API calls
        self._ssl_verify = False      # default as true
        self._device_mgmt_id =  None
        #self._imapObj = ImapLibrary()    # Instantiate the Imap library clas




    def get_last_response_headers(self):
        """ Get the last API call  response's HTTP headers.

        :return:  the last API call  response's HTTP headers
        """
        if (self._session != None):
            return self._session.last_resp.headers
        else:
            return None

    def get_last_request_headers(self):
        """
        :return:  last HTTP API call  request's headers.
        """
        if (self._session != None):
            return self._session.last_resp.request.headers
        else:
            return None

    def get_headers(self):
        """
          Get the default headers which was built when call the keyword:
            Create_Api_Test_Environment
        :return: Return the default headers with Content-Type: 'application/json'
        """

        return self._headers


    def get_current_URL(self):
        """Get the current API's full  URL.

        :return: API URL
        """
        return  self.current_URL

    def get_session(self):
        """
        Get the session object.
        :return: A session object
        """
        return  self._session

    def get_session_cookies(self):
        """
        Returns a key/value dictionary from a session Cookie
        :return: a key/value dictionary
        """
        cookies_jar = self._session.cookies
        cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
        return  cookies_dict

    def get_epoch_time(self):
        """
        Get the Epoch time which is the time in seconds since the UNIX epoch i.e. 00:00:00.000 (UTC) 1 January 1970
        :return: Epoch time
        """
        etime = time.time()
        etime = int(etime)
        return str(etime)

    def create_api_test_environment(self, user, pwd, base_url):
        """Create the API testing environment with User name and password, and base URL

        :param user: user name string
        :param pwd:   user password
        :param base_url: base URL for all the API calls such as: http://admin.dev.linksdwan.com
        :return: None  or  failure will raise  an exception.

        Example::

        | Create Api Test Environment | ${USR_NAME} | ${PASS_WORD} | ${URL} |
        """
        self._user = user
        self._password = pwd
        self.base_url = base_url
        
        coki = self._get_cookie(user, pwd, url= self.base_url)
        logger.console('cookie =  %s'% (coki))

        
        #tok = self._get_csrf_token()
        #logger.info('token =   %s'% (tok))
        headers = self._build_default_headers(coki)
        logger.info ("Just finish Build_Default_Headers: ")
        logger.info(headers)
        

        self._session = requests.Session()   ## create a seesion
    

    
    def post_request(self,resource, payload=None, content_type='application/json;charset=utf-8', files_dict={}, expected_status_code=200, expected_failure=False, json_response=True, timeout_inout=90, allow_redirects=None):
        """Wrapper method for HTTP POST Request.

        :param resource:  resource specified by swaggeer like: proxy/major/api/pops
        :param payload: json data that will be sent as POST data
        :param files_dict: a dictionary of "file full path name: content-type",
                        such as: files_spec = {'file_xml.xml': 'application/xml', 'address.txt': 'text/plain'}
                        A file full path name contains file data to POST to the server
        :param content_type: if content_type is not equal to the default type:'application/json;charset=utf-8’,
                            the header should be changed for using different content_type
        :param expected_status_code: the caller's expected_status_code with the default as: 200
        :param expected_failure: This is for negative testing. The caller expects this  post request fail but do not want to get
                        the exception to fail the test since the caller expects to get status_code=400. The default is: expected_failure=False
        :param timeout_input: How long to wait for getting POST request response from the server before giving up. The default is 90 seconds.
        :param allow_redirects: default is None
        :return: response status and json data if json_response==true and content_type='application/json'. Otherwise return HTTP response object

        Example::

        | ${files_dict} | Evaluate | {'file_xml.xml': 'application/xml', 'address.txt': 'text/plain'} |
        | ${status_code}   ${jdata} = | Post_Request | /proxy/major/api/pops | ${payload} | ${content_type} |  ${files_dict} |
        """
        uri = self._get_url(resource)
        #uri='http://admin.dev.linksdwan.com/'+resource

        ## build the request headers,
        post_headers = self._build_headers_by_content_type(content_type)
        
        '''
        if len(files_dict) ==0:
            files = {}
        
        try:
            if type(payload)!=str:
                payload=str(payload)
                resp=self._session.post(uri,data=payload,  headers=post_headers,files=files,verify=self._ssl_verify,timeout=timeout_inout,allow_redirects=allow_redirects)
            else:
                # There are file(s) for uploading with this post request
                resp=self._post_multiple_multipart_encoded_files(uri, files_dict)
        except Exception as e:
            logger.warn(str(e))
        '''
        files=files_dict
        
        try:
            if payload!=None and type(payload)!=str:
                payload=json.dumps(payload)
            resp=self._session.post(uri,data=payload, headers=post_headers,files=files,verify=self._ssl_verify,timeout=timeout_inout,allow_redirects=allow_redirects)
        except Exception as e:
            logger.warn(str(e))

        if resp.status_code not in (200, 201):
        #rif resp.status_code != expected_status_code:
            #200 OK
            #201 Created - The POST request was successful and the resource is returned as JSON
            if (expected_failure == False):   ## raise exception
                logger.warn(resp.content)
                resp.raise_for_status()     ## A Positive test fails, raises stored HTTPError

        jdata = resp.text           #resp.content
        if len(files_dict) ==0:
            if resp.content:
                ## Fetching response in JSON
                #=json.loads(resp.content),the json-encoded content of a response, if any.
                if json_response==True:
                    jdata = resp.json()
        '''
        # Store the last response object
        #self._session.last_resp = resp
        if json_response==True: #and content_type=='application/json':
            return  (resp.status_code, jdata)
        else:
            return resp
        '''
        #new add
        if json_response is not True:   # no need to convert to Json format and just return the whole reponse object
            return resp
        else:
            return  (resp.status_code, jdata)


    
    def get_request(self, resource, params={}, expected_failure=False, allow_redirects=None, timeout_input=60,json_response=True):
        """Wrapper for HTTP GET request API call.

        :param resource: resource specified by swaggeer such as: /proxy/major/api/agents
        :param params:  Query parameters: such as: ?upperRelationId.equals=0&sort=id,desc&page=0&size=999
        :param expected_failure: This is for negative testing. The caller expects this request fail but do not want to get
                        the exception to fail the test since the caller expects to get status_code=400. The default is: expected_failure=False
        :param allow_redirects:
        :param timeout_input:  optional) How long to wait for the server to send data before giving up. The default is 60 seconds
        :param json_response:  specify if the response data will be  json data, default is True
        :return:  response status and json data if json_response==true. If json_response==false, return the whole response object.

        Example::

        | ${status_code}  ${jdata}= | Get_Request | /proxy/major/api/agents?upperRelationId.equals=0&sort=id,desc&page=0&size=999 |
        """

        redir = True if allow_redirects is None else allow_redirects

        uri = self._get_url(resource)
        logger.info(uri)
        #headers=self._headers
        #logger.info(headers)

        try:
            resp = self._session.get(uri,
                                    headers=self._headers,
                                    params=params,
                                    verify=self._ssl_verify,
                                    timeout=timeout_input )
        except requests.exceptions.RequestException as e:
            logger.warn(str(e))
            resp.raise_for_status()

       # if resp.status_code != 200:
        if resp.status_code >= 400 and resp.status_code < 600:
            if (expected_failure==False):  ## raise exception
                logger.warn(resp.headers)
                logger.warn(resp.content)
                resp.raise_for_status()     ## Raises stored HTTPError
        ## store the last response object
        self._session.last_resp = resp

        if json_response is not True:   # no need to convert to Json format and just return the whole reponse object
            return resp
        else:
            ## Fetching response in JSON
            jdata = resp.json()   #json.loads(resp.content), the json-encoded content of a response, if any.
            return  (resp.status_code, jdata)

    

   
    def put_request(self, resource, data=None, content_type='application/json;charset=utf-8', no_response_content=False,
                    expected_failure=False, timeout_input=60):
        """Wrapper method for HTTP PUT Request.

        :param str resource: resource specified by swaggeer
                        such as: /proxy/major/api/pops
                         
        :param data: data being sent with the request.
        
        :param str content_type: if content_type is not equal to the default
            type:'application/json’, the header should be changed for using a
            different content_type.

        :param bool no_response_content: Default False;
        :param bool expected_failure: This is for negative testing. The caller
            expects this request fail but do not want to get the exception to
            fail the test since the caller expects to get status_code=400.
            The default is: expected_failure=False
            
        :param timeout_input: How long to wait for getting PUT request response
            from the server before giving up. The default is 60 seconds.
            
        :returns: a tuple of  (resp.status_code, resp.json()  )if ( content_type=='application/json'),
                otherwise return  (resp.status_code, resp.content). 
		        If No response data are available, only status will be returned

        Example::

        | ${Resource_URI} |  /agent/#/manage/task?status=&tenantId=&queryCondition=&page_current=1 |
        | ${status_code} | ${jdata}= | Put_Request | ${Resource_URI} | ${payload} |
        """

        ## build the request headers,pwd
        put_headers = self._build_headers_by_content_type(content_type)

        if type(data)!=str:
            data=json.dumps(data)

        resp = self._session.put(self._get_url(resource),
                                 data=data,
                                 headers=put_headers,
                                 verify=self._ssl_verify,
                                 timeout=timeout_input)

        ## Store the last response object
        self._session.last_resp = resp

        if (no_response_content):
            return  resp.status_code

        if resp.status_code != 200:
             if expected_failure==False:  ## raise exception
                logger.warn(resp.status_code)
                logger.warn(resp.text)
                resp.raise_for_status()     ## Raises stored HTTPError

        if content_type=='application/json;charset=utf-8':
            return (resp.status_code, resp.json())
        else:
            return (resp.status_code, resp.text)


    def delete_request(self, resource,  data=(), expected_failure=False, timeout_input=60):
        """Wrapper Method for Send a DELETE request on the session object.

        :param resource: specified in the swagger specification such as: /proxy/major/api/pops/{id}
        :param data:
        :param expected_failure: This is for negative testing. The caller expects this request fail but do not want to get
                    the exception to fail the test since the caller expects to get status_code=400. The default is: expected_failure=False
        :param timeout_input: The time out for getting response. The default is 60 seconds
        :return: HTTP response from Delete operation.

        Example::

        | ${resp}=  | Delete Request  | /proxy/major/api/pops/{id} | timeout_input=30 |
        """

        resp = self._session.delete(self._get_url(resource),
                                    data=data,
                                    headers=self._headers,
                                    verify=self._ssl_verify,
                                    timeout=timeout_input)

        if resp.status_code != 200:
             if (expected_failure==False):  ## raise exception
                logger.warn(resp.content)
                resp.raise_for_status()

        # store the last response object
        self._session.last_resp = resp
        return resp



    def post_multipart_encoded_files_toolbelt(self,resource,file_paths_dict):
        """
            Uploading multiple files in a single request using  requests-toolbelt modul
        :param resource: resource specified by swaggeer like: /proxy/major/api/equipment/import
        :param file_paths_dict: A dictionary of file-full-path-name/content-type: suc has:
                file_paths_dict = {'file_xml.xlsx': 'text/xlsx', 'file_text.txt': 'plain/text','logo.png': 'image/png'}
        :return: http Post response

            The Example with only one XML file:
                ## Create a  dictionary of file-full-path-name/content-type
            | ${file_paths_dict} = |   Create Dictionary  ${MAP_XML_FILE_PATH}/${filename}=text/xlsx |
            | ${resp}= |  Post_Multipart_Encoded_Files_Toolbelt | /proxy/major/api/equipment/import | ${file_paths_dict} |
        """

        #raise   AssertionError("This keyword is NOT supported with a server error 500. Please use the keyword:File Upload Post")
        uri = self._get_url(resource)
        
        # Convert dictionary to list of tuples.
        file_paths_list = list(file_paths_dict.items())
        filename=os.path.basename(file_paths_list[0][0])
        file_dict=file_paths_list[0][0]
        file_type=file_paths_list[0][1]
        fields_input={"file":(filename,open(file_dict,"rb"),file_type)}

        m = MultipartEncoder(fields=fields_input)
        
        post_headers = self._build_headers_by_content_type(m.content_type)

        '''
        #post_headers = self.get_last_request_headers()
        post_headers=self.get_last_request_headers()
        post_headers["Content-Type"] = m.content_type

        ## For Debugging only
        last_response_headers = self.get_last_response_headers()
       # print 'last_response_headers["Set-Cookie"]:  '
        #print  last_response_headers["Set-Cookie"]
        last_response_cookies =  self._session.last_resp.cookies      #A CookieJar of Cookies the server sent back.
       # print   "Last response cookies:  "
       # print   last_response_cookies
        cookies_jar = self._session.cookies
        cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
    
        post_headers["Cookie"] = cookies_dict
        '''

        resp = self._session.post(uri, data=m,
                            verify=self._ssl_verify,
                            headers=post_headers )
        
        self._headers['Content-Type']='application/json;charset=utf-8'
        if resp.status_code not in (200, 201):
            #200 OK
            #201 Created - The POST request was successful
            logger.warn(resp.headers)
            logger.warn(resp.content)
            resp.raise_for_status()     ## A Positive test,
        #jdata = resp.json     #Returns the json-encoded content of a response, if any.
        return   resp




    def get_id_by_other_message(self,jsondata,msg,msg_value):

        '''Return the value of id when we know the value of another message in the dictionary /json list.
        
        :param jsondata: the JSON string or dict or list,which is iterable
        
        :param str msg: the message which is already known.
        
        :param str msg_value: the value of message.
        
        :returns: value(s) of x. If only one value got, return it, or else return
            matched values list.
            
        Note::
        
            the default type of message and value is string.
        
        Example::
        
        
        | ${device_id}=	| Get Id By Other Message | ${json} | equipmentName | E201201922294091 |
        
        '''
        id=''
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
                        logger.warn(e)
                        logger.warn('can not get id')
                                


    def _get_cookie(self, user, pwd, url='http://admin.dev.linksdwan.com'):    #url=http://admin.dev.linksdwan.com/proxy/auth/login
   
        payload={}
        payload["username"],payload["password"]=user,pwd
        data="'"+ json.dumps(payload) + "'"

        cmd='curl -H "Content-Type: application/json"  -X POST -d '+data+' -k %s/proxy/auth/login' % url
        
        logger.info(cmd, also_console=True)
        logger.info("IN ---> _get_cookie() call: ")

        try:
            status,output = subprocess.getstatusoutput(cmd)
            if output:
                result = re.findall(r'"access_token".*"',output)
                cookie = json.loads('{'+str(result)[2:-2]+'}')
                #access_token=cookie['access_token']
                cookie=cookie['access_token']
                logger.info(cookie)
            else:
                raise AssertionError("Fail To Get cookie")
        except:
            raise AssertionError("Fail to get cookie")

        self.cookie = cookie
        #print(cookie)
        return cookie


    def _build_default_headers(self,cookie):
        headers = {}
        #headers["Authorization"] = cookie
        headers["Cookie"]="access_token="+cookie
        headers["Content-Type"] = 'application/json;charset=utf-8'
        self._headers = headers
        return headers


    def _get_url(self,uri):
        '''
        :param uri: resource
        :return: full url path for the API call
        '''
        if uri:
            slash = '' if uri.startswith('/') else '/'

        logger.info("_get_url")
        logger.info('Base_url:  %s'% (self.base_url), also_console=True)

        url = "%s%s%s" %(self.base_url, slash, uri)

        logger.info('Full API URL -->  %s'% (url), also_console=True)

        self.current_URL = url
        return url


    def _build_headers_by_content_type(self, content_type):
        """
           To rebuild the headers if content_type that is not the default 'application/json'
        :param content_type: string input such as:  'application/xml'
        :return: response headers
        """
          ## check if we can use the default headers
        headers = self._headers
        if content_type is None:
            del headers["Content-Type"]
        elif (content_type != 'application/json;charset=utf-8'):   ## check if we can use the default headers
            headers["Content-Type"] = content_type
        #print('\n headers: \n',headers)
        return headers
        
    
    def _post_multiple_multipart_encoded_files(self,uri, files_dict):
        pass



if __name__=='__main__':
    test=API_Test_Lib()
    test.create_api_test_environment("admin","sdwan123!@#","http://admin.dev.linksdwan.com")
    #print(test.create_api_test_environment("admin","sdwan123!@#","http://admin.dev.linksdwan.com"))
    #print(test.get_request('/proxy/major/api/agents','upperRelationId.equals=0&sort=id,desc&page=0&size=999'))
    #payloads={"name":"pop_test","country":"中国","province":"云南省","city":"临沧市","latitude":"23.8878061038","longitude":"100.092612914","details":"del later"}
    #print(test.post_request('/proxy/major/api/pops',payload=payloads,content_type='application/json;charset=utf-8'))
    #print(test.post_request('/proxy/major/api/equipment/import',content_type='application/json;charset=utf-8',files_dict={"sn.xlsx":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","address.txt":"/home/sdwan/Test/Test"}))
    #print(test.delete_request('/proxy/major/api/pops/25'))
    #payload={"name":"pop_test1","country":"中国","province":"云南省","city":"临沧市","latitude":"100.092612914","longitude":"100.092612914","details":"test put func1","id":35}
    #print(test.put_request('proxy/major/api/pops',data=payload))
    #r=test.post_multipart_encoded_files_toolbelt(resource="/proxy/major/api/equipment/import",file_paths_dict={"/home/sdwan/Test/Test/sn.xlsx":"text/xlsx"})
    #print(r)