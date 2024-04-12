from paramiko import SSHClient
import numpy as np
ssh = SSHClient()
ssh.load_system_host_keys()
username = "pageot"

ssh.connect('cupid-login.lngs.infn.it', username = username)
change_directory_command = 'cd /data2/shared_scratch/forMathieu/'
sftp = ssh.open_sftp()

# Specify the remote file path
remote_file_path = 'blabla.txt'

# Specify the local file path where you want to save the file
local_file_path = '/local/home/mp274748/Documents/data/temp/temp.txt'

# Download the file from the remote server
sftp.get(remote_file_path, local_file_path)

# Close the SFTP session
sftp.close()
data = np.loadtxt(local_file_path,delimiter=",")

    # Print the loaded data
print(data)
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(change_directory_command+' && ls')

# Check if ssh_stdout is not None before printing
if ssh_stdout is not None:
    # Read and print the output
    output = ssh_stdout.read().decode().strip()
    print(output)
else:
    print("No output received from the command.")

# Close the SSH connection
ssh.close()