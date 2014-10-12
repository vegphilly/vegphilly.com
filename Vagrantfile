# -*- mode: ruby -*-

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "chef/debian-7.4"

  # for selenium tests
  config.ssh.forward_x11 = true

  # for the gunicorn server
  config.vm.network :forwarded_port, guest: 80, host: 8080
  # for a detached development server
  config.vm.network :forwarded_port, guest: 8888, host: 8888
  # for development use
  config.vm.network :forwarded_port, guest: 8000, host: 8000

  config.vm.synced_folder ".", "/usr/local/vegphilly"

  config.vm.provision :shell do |shell|
    shell.path = "utils/provision_locally.py"
    shell.args = "vagrant /usr/local/vegphilly/ansible/site.yml /usr/local/vegphilly"
  end

  config.vm.provider :virtualbox do |vb, override|
    mem = ENV['VAGRANT_MORE_MEMORY']
    if mem
        print "running vagrant with extra memory: " + mem + "MB\n"
        vb.customize ["modifyvm", :id, "--memory", mem]
    else
      print "NOTE: set the environment variable 'VAGRANT_MORE_MEMORY' to a number to use more RAM.\n"
    end

  end

end
