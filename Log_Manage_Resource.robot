*** Settings ***
Library           String
Library           Collections
Library           LogManage/LogManage.py

*** Keywords ***
get_subnet_mask
    [Arguments]    ${ip_addr}    ${mask}
    ${segment_mask}    Get Segment    ${ip_addr}    ${mask}
    ${ip_network}    get from list    ${segment_mask}    0
    ${mask_num}    get from list    ${segment_mask}    1
    [Return]    ${ip_network}    ${mask_num}
