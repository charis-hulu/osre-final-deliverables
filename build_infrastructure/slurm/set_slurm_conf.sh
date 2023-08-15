#!/bin/bash

DIR=$(pwd)
floating_ips=$1
fixed_ips=$2
IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"

set_slurm_master(){
    local ip=${splitted_floating_ips[0]}
    scp -i ~/$PRIVATE_KEY_NAME ${DIR}/slurm/set_slurm_master.sh cc@$ip:~/
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@$ip "bash set_slurm_master.sh $fixed_ips"
}


set_slurm_per_slave(){
    local i=$1
    local ip=${splitted_floating_ips[$i]}
    scp -i ~/$PRIVATE_KEY_NAME ${DIR}/slurm/set_slurm_slave.sh cc@$ip:~/
    ssh -i ~/$PRIVATE_KEY_NAME -o StrictHostKeyChecking=no cc@$ip "bash set_slurm_slave.sh $fixed_ips"
}

set_slurm_slaves(){
    for (( i=1; i<${#splitted_floating_ips[@]}; i++ ))
    do 
        set_slurm_per_slave $i &
    done
}

set_slurm_master &
set_slurm_slaves

wait