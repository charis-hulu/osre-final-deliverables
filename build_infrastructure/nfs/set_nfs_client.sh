#!/bin/bash

floating_ips=$1
IFS=',' read -ra splitted_floating_ips <<< "$floating_ips"


mkdir ~/nfs

sudo mount ${splitted_floating_ips[0]}:/home/cc/nfs /home/cc/nfs
