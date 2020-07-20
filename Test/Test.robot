*** Settings ***
Default Tags      API    #Test Setup    Initial_Env_Setup
Resource          ../API_Test_Resource.robot
Library           ../API_Test_Lib/API_Test_Lib.py
Library           Collections
Library           String
Variables         ../../sdwan-auto-case(tester_branch)/public/topo/tb.py

*** Test Cases ***
agents_management
    [Tags]    API
    ${status_code}    ${jdata}=    get request    /proxy/major/api/agents?upperRelationId.equals=0&sort=id,desc&page=0&size=999
    ${payload}    Evaluate    {"company":"autotest","type":"","bandwidth":0,"cost":"0.00","region":"","realName":"","phone":"","login":"autotest@netbank.cn","address":"","domain":"","tsdbUrl":"1.1.1.1"}
    ${status_code}    ${jdata}    post request    /proxy/major/api/agents    ${payload}
    ${id}    Get From Dictionary    ${jdata}    id
    ${status}    delete request    proxy/major/api/agents/${id}

pop_management
    ${payload}    Evaluate    {"name":"pop_test","country":"中国","province":"云南省","city":"临沧市","latitude":"23.8878061038","longitude":"100.092612914","details":"del later"}
    ${status_code}    ${jdata}    post request    proxy/major/api/pops    ${payload}
    ${id}    Get From Dictionary    ${jdata}    id
    ${put_payload}    Evaluate    {"name":"pop_test","country":"中国","province":"云南省","city":"临沧市","latitude":"100.092612914","longitude":"100.092612914","details":"test put function","id":${id}}
    ${put_status}    ${p_jdata}    put request    proxy/major/api/pops    ${put_payload}
    ${get_status}    ${g_jdata}    get request    proxy/major/api/pops?size=10&page=0&sort=id,desc
    ${content}    Get From Dictionary    ${g_jdata}    content
    ${edit_info}    Get From List    ${content}    0
    Log    ${edit_info}
    ${del_status}    delete request    /proxy/major/api/pops/${id}
    ${check_status}    ${check_jdata}    get request    proxy/major/api/pops?size=10&page=0&sort=id,desc
    Log    ${check_jdata}

equipment_management
    reload library    Api_Test_Lib
    get equipment info
    ${file_full_path}    Create Dictionary    /home/sdwan/Test/Test/sn.xlsx=text/xlsx
    ${post_resource}    set variable    proxy/major/api/equipment/import
    ${resp}    Post Multipart Encoded Files toolbelt    ${post_resource}    ${file_full_path}
    ${info}    get equipment info
    log    ${info}
    ${id}    get id by other message    ${info}    equipmentName    E20120191119Test
    ${del_status}    delete request    /proxy/major/api/equipment/${id}
    get equipment info

pipeline_test
    #${agent_id }    Add new agent
    ${equipment_id}    import equipment
    #${id}    set value    ${equipment_id}
    allocate equipment to agent    ${equipment_id}
    #comment    test fail due to bad request-->payload JSON parse error
    #release test resources

clear_env
    ${del_status}    delete request    /proxy/major/api/equipment/

upload_version
    reload library    Api_Test_Lib
    Create Api Test Environment    ${NMS.ADMIN_USERNAME}    ${NMS.ADMIN_PASSWORD}    ${NMS.URL}
    ${status}    ${content}    Post file upload    proxy/major/api/file/upload    /home/sdwan/Downloads/E201-v3.2.4-3.4.0-3-g659b817-20200701_DEBUG.zip=application/zip
    ${id}    get from dictionary    ${content}    id
    ${extInfo}    get from dictionary    ${content}    extInfo
    ${versionNumber}    get from dictionary    ${extInfo}    versionNumber
    set to dictionary    ${extInfo}    image=${id}
    ${version_existed}    run keyword and return status    list should contain value    ${version}    ${versionNumber}
    run keyword unless    ${version_existed}    upload confirm    ${extInfo}
    ${cpe_list}    create list    ${CPE1.SN}    ${CPE2.SN}
    Create Api Test Environment    ${NMS.AGENT_USERNAME}    ${NMS.AGENT_PASSWORD}    ${NMS.URL}
    ${payload}    create dictionary    snList=${cpe_list}    version=${versionNumber}
    ${status}    ${batchUp}    post request    proxy/major/api/equipment/batchUp    payload=${payload}
    Log    ${batchUp}
    ${mainTaskId}    get from dictionary    ${batchUp}    mainTaskId
    ${status}    ${jdata}    get request    proxy/configuration/api/device-config-histories?size=10&page=0&sort=id,desc&queryCondition=${mainTaskId}
    Log    ${jdata}

get versions
    reload library    Api_Test_Lib
    Create Api Test Environment    ${NMS.ADMIN_USERNAME}    ${NMS.ADMIN_PASSWORD}    ${NMS.URL}
    ${status}    ${jdata}    get request    proxy/major/api/versions?size=999&sort=id,desc
    ${version}    get value from jsondata    ${jdata}    versionNumber    all=${true}
    Log    ${version}

*** Keywords ***
Get_equipment_info
    ${resource}    set variable    proxy/major/api/equipment?size=10&page=0&sort=id,desc&status.in=%E6%9C%AA%E5%88%86%E9%85%8D%E4%BB%A3%E7%90%86%E5%95%86
    ${status_code}    ${jdata}    get request    ${resource}
    ${equipment_info}    get from dictionary    ${jdata}    content
    [Return]    ${equipment_info}

Add new agent
    ${payload}    Evaluate    {"company":"autotest","type":"","bandwidth":0,"cost":"0.00","region":"","realName":"","phone":"","login":"autotest@netbank.cn","address":"","domain":"","tsdbUrl":"1.1.1.1"}
    ${status_code}    ${jdata}    post request    /proxy/major/api/agents    ${payload}
    ${agent_id}    Get From Dictionary    ${jdata}    id
    [Return]    ${agent_id}

import equipment
    ${file_full_path}    Create Dictionary    /home/sdwan/Test/Test/sn.xlsx=text/xlsx
    ${post_resource}    set variable    proxy/major/api/equipment/import
    ${resp}    Post Multipart Encoded Files toolbelt    ${post_resource}    ${file_full_path}
    ${info}    get equipment info
    ${equipment_id}    get id by other message    ${info}    equipmentName    E20120191119Test
    [Return]    ${equipment_id}

allocate equipment to agent
    [Arguments]    ${equipment_id}
    #${payload}    Create Dictionary    agentId=${agent_id}    equipmentIds=${equipment_id}
    ${payload}    Create Dictionary    agentId=369    equipmentIds=[${equipment_id}]
    ${status}    ${jdata}    put request    /proxy/major/api/equipment/distribute2Agent    ${payload}
    ${equipment_info}    Get equipment info

upload confirm
    [Arguments]    ${extInfo}
    ${status}    ${jdata}    post request    proxy/major/api/versions    payload=${extInfo}
    should be equal    ${status}    ${201}
