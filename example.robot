*** Settings ***
Resource          /git/RF_Lib/API_Test_Resource.robot
Variables         /git/RF_Lib/API_Test_Lib/personal.py
Library           Cpe_Cli.py
Library           Collections
Library           /git/RF_Lib/API_Test_Lib/API_Test_Lib.py
Resource          ../sdwan-auto-case(tester_branch)/resource/public_resource.robot
Library           String

*** Test Cases ***
cpe parameter modify
    Initial Env Setup
    ${cpe_pattern}    set variable    sn=E201202001090007
    ${cpe_status}    ${cpe_id}    check cpe status    ${cpe_pattern}
    run keyword if    "${cpe_status}" == "未上线"    set_cpe_online    10.201.0.88    root    linkwan    ${cpe_pattern}
    ${file_path}    set variable    /home/sdwan/Test/RF_Lib/API_Test_Lib/wan_config.json
    ${payload}    update jsondata from jsonfile    ${file_path}    wan0    natEnable=${false}    mtu=1500
    cpe wan config modify    ${payload}
    active cpe config    ${cpe_id}

test
    clear console line    2075
    console login    10.201.0.207    2075
    ${ctl}    console exec cmd    swanctl --list-sa
    ${route}    console exec cmd    route
    ${ipsec}    console exec cmd    ipsec status
    write    exit
    Close Connection

og
    ${cpe_id}    set variable    1
    log    {"equipmentId":"${cpe_id}"}
