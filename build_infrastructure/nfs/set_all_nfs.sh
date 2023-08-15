#!/bin/bash

DIR=$(pwd)
echo $DIR
floating_ips=$1
IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"

set_nfs_server(){
    local ip=${splitted_floating_ips[0]}
    scp -i ~/$PRIVATE_KEY_NAME ${DIR}/nfs/set_nfs_server.sh cc@$ip:~/
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@$ip "bash set_nfs_server.sh $floating_ips"
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@$ip " \
    mkdir ~/nfs/Downloads  \
    && mkdir ~/nfs/input_data \
    && mkdir ~/nfs/tools \
    && mkdir ~/nfs/jobs
    "
}


set_nfs_per_client(){
    local i=$1
    local ip=${splitted_floating_ips[$i]}
    scp -i ~/$PRIVATE_KEY_NAME ${DIR}/nfs/set_nfs_client.sh cc@$ip:~/
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@$ip "bash set_nfs_client.sh $floating_ips"
}

set_nfs_clients(){
    for (( i=1; i<${#splitted_floating_ips[@]}; i++ ))
    do 
        set_nfs_per_client $i &
    done
}

set_nfs_server &
set_nfs_clients

wait



