#!/bin/bash

IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"


echo "insatnce0"
ssh -i ~/$PRIVATE_KEY_NAME cc@${splitted_floating_ips[0]}  "echo 'test' >> ~/nfs/check_status_1.txt"

for (( i=1; i<${#splitted_floating_ips[@]}; i++ ))
do 
    echo "instance$i"
    ssh -i ~/$PRIVATE_KEY_NAME cc@${splitted_floating_ips[$i]}  "ls -l ~/nfs/check_status_1.txt"   
done