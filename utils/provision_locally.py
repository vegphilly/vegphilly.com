#!/usr/bin/env python

import os
import sys

# these packages are required to *get* ansible, so cannot
# be installed *through* ansible.
REQUIRED_PACKAGES = ["python-dev", "python-pip"]


def is_installed(package):
    command_template = "dpkg -l | grep 'ii  %s '"
    return_code = os.system(command_template % package)
    return return_code == 0


def install_dependencies():
    if not all(map(is_installed, REQUIRED_PACKAGES)):
        os.system('apt-get update')
        os.system('apt-get install -y %s' % " ".join(REQUIRED_PACKAGES))

    os.system("pip install ansible==1.7")


def run_ansible(user, path, project_dir, app_user):
    os.system("mkdir -p /etc/ansible")
    os.system("echo [dev_servers] > /etc/ansible/hosts")
    os.system("echo localhost >> /etc/ansible/hosts")

    os.system('ansible-playbook %s '
              '--connection=local --user=%s --sudo '
              '--extra-vars "project_dir=%s '
              'app_user=%s db_user=%s db_password=%s"'
              % (path, user, project_dir, app_user, app_user, app_user))

if __name__ == '__main__':
    install_dependencies()
    run_ansible(*sys.argv[1:])
