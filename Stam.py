from Common import *
switch_ip='10.9.95.25'
switch_user='ansible'
switch_password='N3tAutomation!'

ssh_object=SSH(switch_ip,switch_user,switch_password)
ssh_object.ssh_connect_password()
out= ssh_object.ssh_command('show configuration | display json')
ssh_object.ssh_close()

print juniper_config_parser_string(out)
