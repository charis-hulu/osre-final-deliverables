#!/bin/bash

floating_ips=$1
IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"


mkdir ~/nfs

cat << EOF | sudo tee /etc/exports
$(
for (( i=1; i<${#splitted_floating_ips[@]}; i++ ))
do  
    echo "/home/cc/nfs    ${splitted_floating_ips[$i]}(rw,sync,no_root_squash,no_subtree_check)"
done
)
EOF

sudo systemctl restart nfs-kernel-server


for (( i=1; i<${#splitted_floating_ips[@]}; i++ ))
do  
    sudo ufw allow from ${splitted_floating_ips[$i]} to any port nfs
done


