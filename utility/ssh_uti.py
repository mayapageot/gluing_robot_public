from paramiko import SSHClient
import numpy as np
import os
ssh = SSHClient()
ssh.load_system_host_keys()
username = "pageot"

ssh.connect('cupid-login.lngs.infn.it', username = username)
change_directory_command = 'cd /data2/shared_scratch/forMathieu/'


# Specify the remote file path
#remote_file_path = 'blabla.txt'
remote_file_path = '/data2/shared_scratch/Glue_files/240404_122817/CAM1/240404_123614_0000000033.bmp'
def load_file_ssh(ssh,remote_file_path,local_temp=r'C:/temp/temp'):
    sftp = ssh.open_sftp()
    ext = os.path.splitext(remote_file_path)[-1]
    local_file_path = local_temp + ext
    sftp.get(remote_file_path, local_file_path)
    sftp.close()
    return local_file_path
def put_file_ssh(ssh,localfilepath, remotefilepath):
    ftp_client = ssh.open_sftp()
    ftp_client.put(localfilepath, remotefilepath)
    ftp_client.close()
local_file_path = load_file_ssh(ssh,remote_file_path)
#data = np.loadtxt(local_file_path,delimiter=",")

    # Print the loaded data
#print(data)
def do_cmd_ssh(ssh, command):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command+' && ls')

    # Check if ssh_stdout is not None before printing
    if ssh_stdout is not None:
        # Read and print the output
        output = ssh_stdout.read().decode().strip()
        print(output)
    else:
        print("No output received from the command.")

# Close the SSH connection
ssh.close()