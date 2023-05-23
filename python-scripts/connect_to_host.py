# Explicitly provide key and passphrase
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import os

client = SSHClient()
#client.load_system_host_keys()
#client.load_host_keys('~/.ssh/known_hosts')
client.set_missing_host_key_policy(AutoAddPolicy())
# 
# commands = [
#     "sudo yum install amazon-cloudwatch-agent"
# ]
# print(commands)
client.connect(hostname='3.8.187.68', username='ec2-user', key_filename='../testagent.pem')
print(client)
# for command in commands:
#     print("running command: {}".format(command))
#     stdin , stdout, stderr = client.exec_command(command)
#     print(stdout.read())
#     print(stderr.read())

# os.system("ls -l")
# copy the file across
with SCPClient(client.get_transport()) as scp:
    scp.put('chinadatalake/python-scripts/cw-agent-install.sh', '/tmp')

# execute the script
stdin, stdout, stderr = client.exec_command('sh /tmp/cw-agent-install.sh')

if stderr.read() == b'':
    print('Success')
else:
    print('An error occurred')
    print(stderr.read())

client.close()


# sudo /opt/aws/amazon-clouwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-clouwatch-agent/bin/config.json

# scp -i /tmp/testagent.pem ec2-user@ec2-3-8-187-68.eu-west-2.compute.amazonaws.com:config.json /Users/vaibhavsrivastava/Downloads

# scp -i /Users/vaibhavsrivastava/Downloads/testagent.pem testagent.pem ec2-user@ec2-13-42-103-169.eu-west-2.compute.amazonaws.com:/opt/aws/amazon-clouwatch-agent/bin/