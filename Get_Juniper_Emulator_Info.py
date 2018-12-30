from Common import *

virt_setup_parameters={
    'baremetal_guest_ports':['xe-0/0/7', 'xe-0/0/8'],
    'switch_type':'juniper_emulator_sw',
    'switch_ip':'172.16.0.18',
    'switch_user':'ansible',
    'switch_password':'Juniper',
    'tenant_nets':['tempest-shared'],
    'setup':'Virtual_Setup'
}

get_switch_conf_as_json(virt_setup_parameters['switch_ip'],
                        virt_setup_parameters['switch_user'],
                        virt_setup_parameters['switch_password'],
                        virt_setup_parameters['switch_type'])

interface_vlan=juniper_config_parser(conf_data_file)['InterfaceVlan']
for k in interface_vlan.keys():
    print k,'-->',interface_vlan[k]