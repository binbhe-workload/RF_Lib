*** Settings ***
Resource          /git/RF_Lib/API_Test_Resource.robot
Variables         /git/RF_Lib/API_Test_Lib/personal.py
Library           /git/RF_Lib/Cpe_Cli.py
Library           Collections
Library           /git/RF_Lib/API_Test_Lib/API_Test_Lib.py

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
