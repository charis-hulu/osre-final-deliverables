#!/bin/bash
floating_ips=$(cat log/floating_ips.txt)
IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"

for (( i=0; i<${#splitted_floating_ips[@]}; i++ ))
do 
    echo "ubuntu$i ${splitted_floating_ips[$i]}"
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@${splitted_floating_ips[$i]} "sudo systemctl status slurmd | grep 'Active: '"
done