import os
import random
import multiprocessing
import subprocess
import re
import time
import datetime;
from manager import WorkloadManager


def load_sra_ids(path):
    sra_file = open(path, "r")
    content = [line.rstrip() for line in sra_file]
    sra_file.close()
    return content

if __name__ == '__main__':

    start = time.time()
    N = 3
    conf_file = "/etc/slurm/slurm.conf"
    exe_file = "/home/cc/nfs/jobs/align_jobs/bwa_mem/single_bwa.sh"

    sra_ids = load_sra_ids("SRA_Acc_List.txt")
    threads=[2, 4, 8, 16, 32]
    cpus=[2, 4, 8, 16, 32]
    memory=[8, 16, 32, 64]
    # threads = [16, 32]
    # cpus = [16, 32]
    # memory = [8]
    
    metrics = [
        cpus,
        memory,
        threads
    ]
    manager = WorkloadManager(conf_file)
    
    manager.collect_metrics(exe_file, sra_ids, metrics, repeat=N)

    
    
    

#pyslurm.job().submit_batch_job({'script':'myjobscript.sh'})