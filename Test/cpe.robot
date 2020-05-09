*** Settings ***
Library           ../Cpe_Cli.py
Library           SeleniumLibrary

*** Test Cases ***
reset_rpi_interface
    open connection    10.201.0.73
    login    root    123456
    ${eth0_ip}    reset rpi interface ip

selenium
    ${username_field}    set variable    xpath=//input
    ${password_field}    set variable    xpath=//div[2]/div/div/div/input
    open browser    http://admin.dev.linksdwan.com    Firefox
    click element    ${username_field}
    input text    ${username_field}    admin
    input text    ${password_field}    sdwan123!@#
    click button    xpath=//div[@id='app']/div[2]/div[3]/div/div[3]/button
