import os
import paramiko
import time
import subprocess


class SSH():
    def __init__(self, host, user, password):
        self.host=host
        self.user=user
        self.password=password

    def ssh_connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.user, password=self.password)
            return {'Status':True}
        except Exception, e:
            return {'Status':False,'Exception':e}


    def ssh_command(self, command):
        stdin,stdout,stderr=self.client.exec_command(command)
        #stdin.close()
        self.output=''
        self.stderr=''
        for line in stdout.read().splitlines():
            self.output+=line+'\n'
        for line in stderr.read().splitlines():
            self.stderr+=line+'\n'
        return {'Stdout':self.output, 'Stderr':self.stderr}


    def scp_upload(self, src_abs_path, dst_abs_path):
        try:
            file_size=os.path.getsize(src_abs_path)
            ftp = self.client.open_sftp()
            t1=time.time()
            ftp.put(src_abs_path,dst_abs_path)
            t2=time.time()
            return {'Status':True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception, e:
            return {'Status':False,'Exception':e}

    def scp_download(self,remote_abs_path,local_abs_path):
        try:
            ftp=self.client.open_sftp()
            t1 = time.time()
            ftp.get(remote_abs_path, local_abs_path)
            t2 = time.time()
            file_size=os.path.getsize(local_abs_path)
            return {'Status': True,'AverageBW':file_size/(t2-t1),'ExecutionTime':t2-t1}
        except  Exception, e:
            return {'Status': False, 'Exception': e}

    def ssh_close(self):
        self.client.close()

def exec_command_line_command(command):
    try:
        command_as_list = command.split(' ')
        command_as_list = [item.replace(' ', '') for item in command_as_list if item != '']
        result = subprocess.check_output(command, shell=True)
        json_output = None
        try:
            json_output = json.loads(result.lower())
        except:
            pass
        return {'ReturnCode': 0, 'CommandOutput': result, 'JsonOutput': json_output}
    except subprocess.CalledProcessError as e:
        print e
        return {'ReturnCode': e.returncode, 'CommandOutput': str(e)}

