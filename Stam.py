from Common import *
switch_ip='10.9.95.25'
switch_user='ansible'
switch_password='N3tAutomation!'

ssh_object=SSH()
ssh_object.ssh_connect_password(switch_ip,switch_user,switch_password)
print ssh_object.ssh_command('show configuration | display json')
ssh_object.ssh_close()
