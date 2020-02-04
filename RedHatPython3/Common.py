import os
import paramiko
import time
import subprocess
import json
import urllib.request, urllib.parse, urllib.error


not_supported_logs=[]

class SSH():
    def __init__(self, host, user, password='', key_path=''):
        self.host=host
        self.user=user
        self.password=password
        self.key_path=key_path

    def ssh_connect_password(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, password=self.password)
            return {'Status':True}
        except Exception as e:
            print_in_color(str(e),'red')
            return {'Status':False,'Exception':e}

    def ssh_connect_key(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, key_filename=self.key_path)
            return {'Status':True}
        except Exception as e:
            print_in_color(str(e), 'red')
            return {'Status':False,'Exception':e}


    def ssh_connect_key(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, key_filename=self.key_path)
            return {'Status':True}
        except Exception as e:
            return {'Status':False,'Exception':e}


    def ssh_command(self, command):
        print_in_color(self.ip+'--> '+command,'blue')
        stdin,stdout,stderr=self.client.exec_command(command)
        #stdin.close()
        self.output=''
        self.stderr=''
        for line in stdout.read().decode().splitlines():
            self.output+=line+'\n'
        for line in stderr.read().decode().splitlines():
            self.stderr+=line+'\n'
        result= {'Stdout':self.output, 'Stderr':self.stderr}
        if len(result['Stderr'])!=0 and 'warning' in str(result['Stderr']).lower():
            print_in_color(result['Stderr'],'yellow')
        else:
            print_in_color(result['Stderr'], 'red')
        return result


    def ssh_command_only(self, command):
        self.stdin,self.stdout,self.stderr=self.client.exec_command(command)
        return {'Stdout':self.stdout.read().decode(),'Stderr':self.stderr.read().decode()}

    def scp_upload(self, src_abs_path, dst_abs_path):
        try:
            file_size=os.path.getsize(src_abs_path)
            ftp = self.client.open_sftp()
            t1=time.time()
            ftp.put(src_abs_path,dst_abs_path)
            t2=time.time()
            return {'Status':True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception as e:
            print_in_color(str(e), 'red')
            return {'Status':False,'Exception':e}

    def scp_download(self,remote_abs_path,local_abs_path):
        try:
            ftp=self.client.open_sftp()
            t1 = time.time()
            ftp.get(remote_abs_path, local_abs_path)
            t2 = time.time()
            file_size=os.path.getsize(local_abs_path)
            return {'Status': True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception as e:
            print_in_color(str(e), 'red')
            return {'Status': False, 'Exception': e}

    def ssh_close(self):
        self.client.close()

def print_in_color(string,color_or_format=None):
    string=str(string)
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    if color_or_format == 'green':
        print(bcolors.OKGREEN + string + bcolors.ENDC)
    elif color_or_format =='red':
        print(bcolors.FAIL + string + bcolors.ENDC)
    elif color_or_format =='yellow':
        print(bcolors.WARNING + string + bcolors.ENDC)
    elif color_or_format =='blue':
        print(bcolors.OKBLUE + string + bcolors.ENDC)
    elif color_or_format =='bold':
        print(bcolors.BOLD + string + bcolors.ENDC)
    else:
        print(string)


def exec_command_line_command(command):
    try:
        print_in_color('--> '+command, 'blue')
        command_as_list = command.split(' ')
        result = subprocess.check_output(command, stdin=True, stderr=subprocess.STDOUT, shell=True,encoding='UTF-8')
        json_output = None
        try:
            json_output = json.loads(result.lower())
        except:
            pass
        return {'ReturnCode': 0, 'CommandOutput': result, 'JsonOutput': json_output}
    except subprocess.CalledProcessError as e:
        print_in_color(command,'red')
        print_in_color(e.output, 'red')
        return {'ReturnCode': e.returncode, 'CommandOutput': e.output}



def profanity_check(text, check_lines_contains_string=None):
    text=str(text).split('\n')
    if check_lines_contains_string!=None:
        text=[line for line in text if check_lines_contains_string.lower() in line.lower()]
    for line in text:
        connection = urllib.request.urlopen("http://www.wdylike.appspot.com/?q="+urllib.parse.quote(line))
        output = connection.read()
        connection.close()
        if "true" in output:
            return {'ProfanityCheckResult':True, 'Failed_Line':line}
    return {'ProfanityCheckResult':False, 'Failed_Line':None}




def collect_log_paths(log_root_path):
    logs=[]
    for root, dirs, files in os.walk(log_root_path):
        for name in files:
            if '.log' in name:
                file_abs_path=os.path.join(os.path.abspath(root), name)
                if os.path.getsize(file_abs_path)!=0 and 'LogTool' not in file_abs_path:
                    to_add = True
                    for item in not_supported_logs:
                        if item in file_abs_path:
                            to_add = False
                    if to_add==True:
                        logs.append(file_abs_path)
    logs=list(set(logs))
    return logs

def spec_print(string_list):
    len_list=[]
    for item in string_list:
        len_list.append(len('### '+item.strip()+' ###'))
    max_len=max(len_list)
    print('')
    print("#"*max_len)
    for item in string_list:
        print("### "+item.strip()+" "*(max_len-len("### "+item.strip())-4)+" ###")
    print("#"*max_len+'\n')

def juniper_config_parser(path_to_config_json):
    json_output=json.loads(open(path_to_config_json,'r').read().lower())
    interfaces=json_output['configuration']['interfaces']['interface']
    int_vlan_dic={}
    for inter in interfaces:
        inter_vlans=None
        name=inter['name']
        try:
            inter_vlans=inter['unit'][0]['family']['ethernet-switching']['vlan']
        except Exception as e:
            print(e)
        int_vlan_dic[name]=inter_vlans
    vlans=json_output['configuration']['vlans']
    return {'Interfaces':interfaces,'Vlans':vlans, 'InterfaceVlan':int_vlan_dic}

def get_switch_conf_as_json(ip,user,password,sw_type=None):
    #types: juniper_physical_sw juniper_emulator_sw
    if sw_type=='juniper_physical_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
        json_output=json.loads(str(out))
        vlans=json_output['configuration']['vlans']
        interfaces=json_output['configuration']['interfaces']['interface']
        int_vlan_dic={}
        for inter in interfaces:
            inter_vlans=None
            name=inter['name']
            try:
                inter_vlans=inter['unit'][0]['family']['ethernet-switching']['vlan']
            except Exception as e:
                print(e)
            int_vlan_dic[name]=inter_vlans
        return {'Interfaces':interfaces,'Vlans':vlans, 'InterfaceVlan':int_vlan_dic}

    if sw_type=='juniper_emulator_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
        json_output = json.loads(str(out))
        vlans = json_output['configuration'][0]['vlans']
        interfaces = json_output['configuration'][0]['interfaces'][0]['interface']
        int_vlan_dic = {}
        for inter in interfaces:
            inter_vlans = None
            name = inter['name']['data']
            try:
                inter_vlans = inter['unit'][0]['family'][0]['ethernet-switching'][0]['vlan'][0]
            except Exception as e:
                print(e)
            int_vlan_dic[name] = inter_vlans
    return {'Interfaces': interfaces,'Vlans':vlans,'InterfaceVlan':int_vlan_dic}

def get_switch_configuration_file(ip,user,password,sw_type=None):
    print(ip,user,password,sw_type)
    #types: juniper_physical_sw juniper_emulator_sw
    if sw_type=='juniper_physical_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
    if sw_type=='juniper_emulator_sw':
        command = 'show configuration | display json'
        ssh_object = SSH(ip, user, password)
        ssh_object.ssh_connect_password()
        out = ssh_object.ssh_command_only(command)['Stdout']
        ssh_object.ssh_close()
    return out

def get_juniper_sw_get_port_vlan(ip, user, password, ports):
    ssh_object = SSH(ip, user, password)
    ssh_object.ssh_connect_password()
    result_dic={}
    for port in ports:
        try:
            command='show configuration interfaces '+port
            out=ssh_object.ssh_command_only(command)['Stdout']
            vlans=[line.split('members')[1].strip(';').replace('[','').replace(']','') for line in out.split('\n') if 'members' in line]
            vlans=[item for item in vlans[0].split(' ') if item!='']
            result_dic[port]=vlans
        except:
            result_dic[port]=None
    ssh_object.ssh_close()
    return result_dic

def run_command_on_switch(ip, user, password, command):
    ssh_object = SSH(ip, user, password)
    ssh_object.ssh_connect_password()
    out=ssh_object.ssh_command_only(command)
    ssh_object.ssh_close()
    print(out)
    return out

def delete_server(source_overcloud, ids_list, timeout=600):
    for id in ids_list:
        exec_command_line_command(source_overcloud + 'openstack server delete ' + id)
    existing_server_ids = [item['id'] for item in exec_command_line_command(source_overcloud + 'openstack server list -f json')['JsonOutput']]
    start_time = time.time()
    to_stop = False
    # Wait till all servers are deleted "
    while to_stop == False and time.time() < (start_time + timeout):
        time.sleep(10)
        list_servers_result = exec_command_line_command(source_overcloud + 'openstack server list -f json')[
            'JsonOutput']
        if len(list_servers_result) != 0:
            names = [item['name'] for item in list_servers_result]
            print('-- Existing servers are: ', names)
        if len(list_servers_result) == 0:
            to_stop = True
    # Return True if no server left, else return False
    return to_stop

def wait_till_bm_is_in_state(source_overcloud, expected_state, timeout=600):
    start_time = time.time()
    to_stop = False
    delay=10
    while to_stop==False and time.time() < (start_time + timeout):
        time.sleep(delay)
        command=source_overcloud+'openstack baremetal node list -f json'
        command_result=exec_command_line_command(command)
        if command_result['ReturnCode']==0:
            actual_states=[item['provisioning state'] for item in command_result['JsonOutput']]
            print('--> Actual Provisioing States are: '+str(actual_states))
            if list(set(actual_states)) == [expected_state]:
                to_stop=True
            if 'clean failed' in actual_states:
                print(actual_states)
                return False
            if 'available' in actual_states:
                timeout-=1
        else:
            print_in_color('Failed to execute: '+command)
    if to_stop==True:
        time.sleep(5) # Adding delay anyway
    return to_stop

def wait_till_servers_are_active(source_overcloud,timeout=600):
    start_time = time.time()
    to_stop = False
    while to_stop == False and time.time() < (start_time + timeout):
        time.sleep(10)
        list_servers_result = exec_command_line_command(source_overcloud + 'openstack server list --all -f json')['JsonOutput']
        statuses = [item['status'] for item in list_servers_result]
        print('--> Server statuses: '+str(statuses))
        if 'error' in statuses:
            return False
        if list(set(statuses)) == ['active']:
            to_stop = True
    return to_stop

def check_ssh(ip, user,password,timeout=300):
    print('check_ssh')
    print(ip, user,password,timeout)
    to_stop=False
    start_time=time.time()
    try_number=0
    while to_stop == False and time.time() < (start_time + timeout):
        try_number+=1
        print('Try number: '+str(try_number))
        print('in while')
        try:
            ssh_object = SSH(ip, user, password)
            print(ssh_object)
            ssh_object.ssh_connect_password()
            print('after ssh connect')
            out = ssh_object.ssh_command_only('date')['Stdout']
            print(out)
            if len(str(out))!=0:
                to_stop=True
            ssh_object.ssh_close()
        except Exception as e:
            print_in_color(str(e), 'red')
        time.sleep(5)
    return to_stop





