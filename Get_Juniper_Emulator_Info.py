from Common import *

# Virtual Setup #
setup_parameters={
    'baremetal_guest_ports':['xe-0/0/7', 'xe-0/0/8'],
    'switch_type':'juniper_emulator_sw',
    'switch_ip':'172.16.0.18',
    'switch_user':'ansible',
    'switch_password':'Juniper',
    'tenant_nets':['tempest-shared'],
    'setup':'Virtual_Setup'
}

json=get_switch_conf_as_json(setup_parameters['switch_ip'],
                        setup_parameters['switch_user'],
                        setup_parameters['switch_password'],
                        setup_parameters['switch_type'])

print json.keys()

interface_vlan=json['InterfaceVlan']
for k in interface_vlan.keys():
    print k,'-->',interface_vlan[k]