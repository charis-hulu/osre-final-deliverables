#!/bin/bash
fixed_ips=$1
IFS=',' read -ra splitted_fixed_ips <<< "$fixed_ips"

n_slaves=$(( ${#splitted_fixed_ips[@]} - 1 ))

cat << EOF | sudo tee /etc/slurm/slurm.conf

# slurm.conf file generated by configurator easy.html.
# Put this file on all nodes of your cluster.
# See the slurm.conf man page for more information.
#
SlurmctldHost=localhost
#
#MailProg=/bin/mail
MpiDefault=none
#MpiParams=ports=#-#
ProctrackType=proctrack/cgroup
ReturnToService=2
SlurmctldPidFile=/var/run/slurmctld.pid
#SlurmctldPort=6817
SlurmdPidFile=/var/run/slurmd.pid
#SlurmdPort=6818
SlurmdSpoolDir=/var/spool/slurm/slurmd
SlurmUser=slurm
#SlurmdUser=root
StateSaveLocation=/var/spool/slurm/
SwitchType=switch/none
TaskPlugin=task/affinity,task/cgroup
#
#
# TIMERS
#KillWait=30
#MinJobAge=300
#SlurmctldTimeout=120
#SlurmdTimeout=300
#
#
# SCHEDULING
SchedulerType=sched/backfill
SelectType=select/cons_res
SelectTypeParameters=CR_Core_Memory
#
#
# LOGGING AND ACCOUNTING
AccountingStorageType=accounting_storage/slurmdbd
ClusterName=cluster
#JobAcctGatherFrequency=30
JobAcctGatherType=jobacct_gather/cgroup
#SlurmctldDebug=info
SlurmctldLogFile=/var/log/slurmctld.log
#SlurmdDebug=info
SlurmdLogFile=/var/log/slurmd.log
#
#
# COMPUTE NODES
$(
    for (( i=1; i<${#splitted_fixed_ips[@]}; i++ ))
    do
        echo "NodeName=instance$i NodeAddr=${splitted_fixed_ips[$i]} CPUs=48 Boards=1 SocketsPerBoard=2 CoresPerSocket=12 ThreadsPerCore=2 RealMemory=112569"
    done
)

PartitionName=test Nodes=instance[1-$n_slaves] Default=YES MaxTime=INFINITE State=UP
# PartitionName=test Nodes=ubuntu0,linux[1-32] Default=YES MaxTime=INFINITE State=UP

# DefMemPerNode=1000
# MaxMemPerNode=1000
# DefMemPerCPU=4000
# MaxMemPerCPU=4096

EOF



sudo systemctl daemon-reload
sudo systemctl restart slurmdbd
sleep 2s
sudo systemctl restart slurmctld