up:
	vagrant up
	$(MAKE) local-ssh-config

destroy:
	vagrant destroy --force

local-ssh-config:
	vagrant ssh-config > .vagrant/ssh-config

ARGS?=
local-provision:
	ansible-playbook -i ansible/inventories/vagrant/hosts.yml ansible/main.yml $(ARGS)
