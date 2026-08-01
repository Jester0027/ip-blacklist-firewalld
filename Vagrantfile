Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.define :server do |server|
    cpus = 2
    memory = 2048
    server.vm.box = "almalinux/10"
    server.vm.box_version = "10.2.20260720"
    server.vm.hostname = "vm.local"
    
    server.vm.provider :libvirt do |libvirt|
        libvirt.qemu_use_session = false
        libvirt.cpus = cpus
        libvirt.memory = memory
    end
  end
end