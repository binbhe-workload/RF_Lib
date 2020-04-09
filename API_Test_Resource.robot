*** Keywords ***
Initial_Env_Setup
    Create Api Test Environment    ${ENV.USERNAME}    ${ENV.PASSWORD}    ${ENV.URL}

check_cpe_status
    [Arguments]    ${pattern}
    ${status_code}    ${json_data}    get request    /proxy/major/api/getCpeList?size=10&page=0&sort=logisticsId,id,desc&tenantId=405&disableStatus=0&status=
    Should Be Equal    ${status_code}    ${200}
    ${cpe_list}    get from dictionary    ${json_data}    content
    ${cpe}    get cpe matches    ${cpe_list}    ${pattern}
    ${cpe_status}    get from dictionary    ${cpe}    status
    ${cpe_id}    get from dictionary    ${cpe}    id
    [Return]    ${cpe_status}    ${cpe_id}

set_cpe_online
    [Arguments]    ${cpe_ip}    ${cpe_username}    ${cpe_password}    ${cpe_pattern}
    open connection    ${cpe_ip}
    login    ${cpe_username}    ${cpe_password}
    #execute command    echo ${host} iot.linkwan.cn >> /etc/host
    ${stdout}    execute command    cat /etc/host
    #should contain    ${host} iot.linkwan.cn    ${stdout}
    close connection
    FOR    ${one}    IN RANGE    100
        ${cpe_status}    ${cpe_id}    check cpe status    ${cpe_pattern}
        Exit For Loop If    "${cpe_status}" == "已上线"
    END

cpe_wan_config_modify
    [Arguments]    ${payload}
    #${file_path}    set variable    /home/sdwan/Test/RF_Lib/API_Test_Lib/wan_config.json
    #${payload}    update jsondata from jsonfile    ${file_path}    wan0    natEnable=${false}    mtu=1500
    ${status_code}    ${jsondata}    put request    proxy/major/api/equipment/configDraft    ${payload}    application/json
    should be equal    ${status_code}    ${200}
    should contain    ${jsondata}    保存成功

active_cpe_config
    [Arguments]    ${cpe_id}
    ${file_path}    set variable    /home/sdwan/Test/RF_Lib/API_Test_Lib/active_cpe_config.json
    ${payload}    update jsondata from jsonfile    ${file_path}    equipmentId=${cpe_id}
    ${status_code}    ${jsondata}    put request    proxy/major/api/equipment/configDraft/apply?equipmentId=${cpe_id}    content_type=${none}    params=${payload}
    should be equal    ${status_code}    ${200}
    FOR    ${one}    IN RANGE    10
        sleep    1
        ${responce_code}    ${jdata}    get request    proxy/configuration/api/device-config-histories?size=10&page=0&sort=id,desc&queryCondition=${jsondata}
        ${status}    get value from jsondata    ${jdata}    status
        Exit For Loop If    ${status}=="SUCCESS"
    END
    should be equal    ${status}    SUCCESS
