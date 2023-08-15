#!/bin/bash

END_DATE="2023-07-29 23:59"
KEY_PAIR_NAME=test-key

n_masters=1
n_slaves=20
start_isnt=0

floating_ips=()
leases_name=()
instances_name=()


create_instance(){
    
    local lease_name=$1
    local instance_name=$2
    local floating_ip=$3
    local image_id=$4

    openstack reservation lease create \
    --reservation min=1,max=1,resource_type=physical:host,resource_properties='["=", "$node_type", "compute_haswell_ib"]' \
    --end-date "$END_DATE" \
    $lease_name

    local reservation_id=$(openstack reservation lease show $lease_name | grep \"id\": | tail -1 | (read h; echo ${h:28:36}))

    openstack server create \
    --image $image_id \
    --flavor baremetal \
    --key-name $KEY_PAIR_NAME \
    --nic net-id=1a03cf65-8fd6-4fce-94fd-bbaabe68a8e1 \
    --hint reservation=$reservation_id \
    $instance_name

    openstack server add floating ip $instance_name $floating_ip
}


set_floating_ips(){
    for (( i=0; i<($n_masters+$n_slaves); i++ ))
    do  
        ip=$(openstack floating ip create public | grep floating_ip_address | (read h; echo ${h:24:15}))
        floating_ips+=("$ip")
    done
}

set_leases(){
    for (( i=${start_isnt}; i<($start_isnt+$n_masters+$n_slaves); i++ ))
    do 
        leases_name+=("lease$i")
    done

}

set_instances(){
    for (( i=${start_isnt}; i<($start_isnt+$n_masters+$n_slaves); i++ ))
    do 
        instances_name+=("instance$i")
    
    done

}

set_floating_ips
set_leases
set_instances

for (( i=0; i<($n_masters+$n_slaves); i++ ))
do 
    lease_name=${leases_name[i]}
    instance_name=${instances_name[i]}
    floating_ip=${floating_ips[i]}
    
   
    if  [ "$instance_name" = "instance0" ]
    then
        image_id=045ac99c-ef80-449b-a09a-add2a68a08af
        echo "$lease_name, $instance_name, $floating_ip, $image_id"
        create_instance $lease_name $instance_name $floating_ip $image_id
    else
        image_id=6e8f9a51-fd91-4fc2-a8f1-bdf4baa0fdfb
        echo "$lease_name, $instance_name, $floating_ip, $image_id"
        create_instance $lease_name $instance_name $floating_ip $image_id
    fi
    
    # echo "slave_$i"
    # ip_addresses[$i-1]="IP_$i"
done

wait

serialized_ips=$(IFS=','; echo "${floating_ips[*]}")
serialized_leases=$(IFS=','; echo "${leases_name[*]}")
serialized_instances=$(IFS=','; echo "${instances_name[*]}")

echo "export floating_ips=\"$serialized_ips\"" >> ~/.bashrc
echo "export leases_name=\"$serialized_leases\"" >> ~/.bashrc
echo "export instances_name=\"$serialized_instances\"" >> ~/.bashrc
source ~/.bashrc
# echo $a
