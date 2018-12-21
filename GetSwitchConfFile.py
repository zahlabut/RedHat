from Common import *
conf_data_file='sw_conf.json'
exec_command_line_command("sshpass -p N3tAutomation! ssh ansible@10.9.95.25 'show configuration | display json' > "+conf_data_file)
interface_vlan=juniper_config_parser(conf_data_file)['InterfaceVlan']
for k in interface_vlan.keys():
    print k,'-->',interface_vlan[k]