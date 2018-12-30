from Common import *

# QE Setup #
qe_setup_parameters={
    'baremetal_guest_ports':['xe-0/0/6', 'xe-0/0/7'],
    'switch_type':'juniper_physical_sw',
    'switch_ip':'10.9.95.25',
    'switch_user':'ansible',
    'switch_password':'N3tAutomation!',
    'tenant_nets':['tenant-net','tenant-net2'],
    'setup':'QE_Setup'
}

json=get_switch_conf_as_json(virt_setup_parameters['switch_ip'],
                        virt_setup_parameters['switch_user'],
                        virt_setup_parameters['switch_password'],
                        virt_setup_parameters['switch_type'])

print json.keys()

interface_vlan=json['InterfaceVlan']
for k in interface_vlan.keys():
    print k,'-->',interface_vlan[k]