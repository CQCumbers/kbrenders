from digitalocean import Manager, Droplet

user_data = '''
#!/bin/sh
add-apt-repository -y ppa:thomas-schiex/blender
apt-get -y update
apt-get -y install blender
apt-get -y install python3-pip
pip3 install pillow boto3 requests

export MAILGUN_KEY={mailgun_key}
git clone --depth 1 {backend_repo} kbrenders-backend
cd kbrenders-backend
python3 {backend_script}
shutdown -h now
'''

manager = Manager(token="secretspecialuniquesnowflake")
keys = manager.get_all_sshkeys()

droplet = Droplet(token="secretspecialuniquesnowflake",
                   name='kbrenders-backend',
                   region='nyc3',
                   image='ubuntu-16-04-x64', # Ubuntu 16.04 LTS
                   size_slug='c2', # Compute droplet, 2 vCPUs
                   ssh_keys=keys, # Copy all SSH keys
                   backups=False
                   user_data=user_data)
droplet.create()
