#!/usr/bin/env python

import os
import sys
import json

# these packages are required to *get* ansible, so cannot
# be installed *through* ansible.
REQUIRED_PACKAGES = ["python-dev", "python-pip", "libffi-dev"]


def is_installed(package):
    command_template = "dpkg -l | grep 'ii  %s '"
    return_code = os.system(command_template % package)
    return return_code == 0


def install_dependencies():
    if not all(map(is_installed, REQUIRED_PACKAGES)):
        os.system('apt-get update')
        os.system('apt-get install -y %s' % " ".join(REQUIRED_PACKAGES))

    os.system("pip install ansible==1.7")


def run_ansible(user, path, project_dir):
    os.system("mkdir -p /etc/ansible")
    with open('/etc/ansible/hosts', 'w') as f:
        f.write('[dev_servers]\n'
                'localhost\n')

    extra_vars = json.dumps({
        'project_dir': project_dir,
        'app_user': user,
        'db_user': user,
        'password': user,
    })

    os.system("ansible-playbook "
              "--sudo "
              "--connection=local %s "
              "--user=%s --extra-vars '%s'"
              % (path, user, extra_vars))

if __name__ == '__main__':
    install_dependencies()
    run_ansible(*sys.argv[1:])
