from Common import *
conf_data_file='sw_conf.json'
#for simulator use: sshpass -p Juniper ssh ansible@172.16.0.18 'show configuration | display json' > stam.txt
exec_command_line_command("sshpass -p Juniper ssh ansible@172.16.0.18 'show configuration | display json' > "+conf_data_file)
interface_vlan=juniper_config_parser(conf_data_file)['InterfaceVlan']
for k in interface_vlan.keys():
    print k,'-->',interface_vlan[k]