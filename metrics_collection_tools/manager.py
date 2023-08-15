import random
import time
import subprocess
import paramiko
import copy
import re
import datetime
from job import Job
from threading import Thread, Lock

class WorkloadManager:
    def __init__(self, conf_path):
        self.conf_path = conf_path
        self.master_node = None
        self.compute_nodes = []
        self.total_jobs = 0
        self.ip_dict = dict()
        self.client_dict = dict()
        # self.monitor_tools = {
        #     'slurm_accounting': SlurmAccounting(),
        #     'top': Top()
        # }
        #self.job_packing_file = self.create_job_packing_file()
        self.logfile = open("all.txt", "w", 1)
        self.finished_jobs=[]
        self.elapsed = 0
        self.start = time.time()
        self.threads = []
        self.pack_id = 0
        self.progress_log = open("progress.txt", "w", 1)
        self.finished_log = open("finished.txt", "w", 1)
        
        self.read_conf()
        self.connect_to_compute_nodes()

        
        
    

    def read_conf(self):
        conf_file = open(self.conf_path, "r")
        lines = conf_file.readlines()

        for line in lines:
            if "NodeName" in line and "NodeAddr" in line:
                node_info = [x for x in re.split("\s+", line) if x != '']
                name = None
                for info in node_info:
                    key, val = info.split("=")
                    if key == "NodeName":
                        self.compute_nodes.append(val)
                        name = val
                    if key == "NodeAddr":
                        self.ip_dict[name] = val


    def connect_to_compute_nodes(self):
        self.log_progress("CONNECTING TO COMPUTE NODES...")
        for node in self.compute_nodes:
            client = paramiko.SSHClient()
            ip_add = self.ip_dict[node]
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip_add, username='cc', key_filename="/home/cc/test-private-key")
            self.client_dict[node] = client

    def get_parsed_squeue(self):
        command = f"squeue"
        result = subprocess.run(command, shell=True, capture_output=True, text=True) 
        output = [x for x in result.stdout.split("\n") if x != ''][1:]
        queue = []
        for row in output:
            stats = [x for x in re.split("\s+", row) if x != '']
            queue.append(stats)
        return queue

    def log_job_stats(self, job, string):
        splitted =  re.split("\s+", string)
        stats = [x for x in splitted if x != '']
        pid = job.pid
        user = None
        priority = None
        nice_val = None
        virtual = None
        res = None
        shr = None
        status = None
        cpu_perc = None
        mem_perc = None
        cpu_time = None
        command = None
        if stats and stats[0] != "PID":
            pid = stats[0]
            user = stats[1]
            priority = stats[2]
            nice_val = stats[3]
            virtual = stats[4]
            res = stats[5]
            shr = stats[6]
            status = stats[7]
            cpu_perc = stats[8]
            mem_perc = stats[9]
            cpu_time = stats[10]
            command = stats[11]
       

        ts = datetime.datetime.now().timestamp()
        #self.logfile
        row = f"{ts},{job.id},{pid},{virtual},{res},{shr},{status},{cpu_perc},{mem_perc},{cpu_time},{command},{job.n_pack},{job.pack_id}"
        lock = Lock()
        with lock:
            self.logfile.write(row)
            self.logfile.write("\n")
   
        #print(row)
        

    def get_job_state(self, job):
        queue = self.get_parsed_squeue()
        state = None
        for stats in queue:
            if stats[0] == job.id:
                state = stats[4]
                break
        return state

    def parse_listpids(self, stdout):
        output = [x for x in re.split("\n",stdout.read().decode('utf-8'))[1:] if x != '']
        listpids = []
        for row in output:
            datum = [x for x in re.split("\s+", row) if x != '']
            job_pid = datum[0]
            job_id = datum[1]
            step_id = datum[2]
            local_id = datum[3]
            global_id = datum[4]
            listpids.append(datum)
        return listpids


    def get_job_pid_from_client(self, job, client):
        time.sleep(5)
       
        if job.pid == None:

            stdin, stdout, stderr = client.exec_command(f'scontrol listpids')
            stdin.close()
            listpids = self.parse_listpids(stdout)
        
            for datum in listpids:
                job_pid = datum[0]
                job_id = datum[1]
                step_id = datum[2]
                local_id = datum[3]
                global_id = datum[4]
                if job_id == job.id and local_id == '-' and global_id == '-':
                    job.pid = job_pid
                    print(f"JOB PID of {job.id} is {job_pid} or {job.pid}:", datum)
                    break
        
        return job.pid



    def monitor_job(self, job, instance):
        client = self.client_dict[instance]

        job_pid = self.get_job_pid_from_client(job, client)
        state = self.get_job_state(job)
        while job_pid == None and (state == "PD" or state == "R"):
            job_pid = self.get_job_pid_from_client(job, client)
            state = self.get_job_state(job)

        # state = self.get_job_state(job)
        if job_pid != None:
            print(f"JOB PID of {job.id} is {job_pid} or {job.pid}")
            stdin, stdout, stderr = client.exec_command(f'python /home/cc/nfs/main/collect_metrics_v2/pstat.py {job.id} {job_pid} {job.n_pack} {job.pack_id} 1')
            stdin.close()
        else:
            print(f"JOB PID of {job.id} is NONE")
        # while state == "PD" or state == "R":
        #     time.sleep(2)
        #     if state == "PD":
        #         continue
        #     elif state == "R":
        #         assert job_pid != None
        #         stdin, stdout, stderr = client.exec_command(f'python pstat.py {job.id} {job_pid}')
        #         stdin.close()
        #         output = stdout.read().decode('utf-8')
        #         self.log_job_stats(job, output) 

        #     state = self.get_job_state(job)

        self.finished_jobs.append(job)
        self.log_job_final_stats(job)
        self.log_progress(f"JOB {job.id} is COMPLETED... {len(self.finished_jobs)}/{self.total_jobs}")

    def log_progress(self, message):
        lock = Lock()
        with lock:
            self.progress_log.write(message)
            self.progress_log.write("\n")


    def log_job_final_stats(self, job):
        command = f"sacct -j {job.id} --format='all' -P"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = [line for line in result.stdout.split("\n")[1:] if line != ""]
    
        lock = Lock()
        with lock:
            for line in output:
                self.finished_log.write(line)
                self.finished_log.write("\n")

    def submit_job(self, exe_file, args, instance, n_pack):
        
        sra_id = args[0]
        thread = args[3]

        alloc_cpu = args[1]
        alloc_mem = args[2]
        inst_id = instance[8:]
        
        job_command = f"sbatch --cpus-per-task={alloc_cpu} --mem={alloc_mem}G --nodelist=instance[{inst_id}] {exe_file} {thread} {sra_id}"
        
        #print("EXE:", exe_file)
        result = subprocess.run(job_command, shell=True, capture_output=True, text=True)
        output = result.stdout.split(" ")
        
        #print(job_command)
        #print("OUTPUT:",result.stdout)

        job_id = output[-1].split("\n")[0]
        self.log_progress(f"PACKING {job_id} to {instance}")
        
        job = Job(
            job_id=job_id, 
            alloc_cpu=alloc_cpu, 
            alloc_mem=alloc_mem, 
            sra_id=sra_id,
            pack_id=self.pack_id,  
            pid=None, 
            n_pack=n_pack,
            thread=thread
        )
        self.monitor_job(job, instance)

        return job_id

    def generate_packing_combination(self, metrics):
        all_possible_args=[]
        for i in range(len(metrics[0])):
            for j in range(len(metrics[1])):
                for k in range(len(metrics[2])):
                    args=[metrics[0][i], metrics[1][j], metrics[2][k]]
                    all_possible_args.append(args)
        thres_cpus=48
        thres_mem=112 # in GB
        random.shuffle(all_possible_args)
        pack_combination=[]
        i = 0
        pack=[]
        total_cpus=0
        total_mem=0
        while i < len(all_possible_args):
            args = all_possible_args[i]
            tmp_cpus = total_cpus + args[0]
            tmp_mem = total_mem + args[1]
            if tmp_cpus <= thres_cpus and tmp_mem < thres_mem:
                #print(i, args)
                pack.append(args)
                total_cpus = tmp_cpus
                total_mem = tmp_mem
                i += 1
            else:
                pack_combination.append(pack)
                total_cpus = 0
                total_mem = 0
                pack = []
        pack_combination.append(pack)
        return pack_combination

    def get_idle_instance(self):
        command = "squeue"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.split("\n")[1:]

        
        instances = copy.deepcopy(self.compute_nodes)

        queue = self.get_parsed_squeue()
        chosen_instance = None
              
        for stat in queue:
            job_id = stat[0]
            partition = stat[1]
            name = stat[2]
            user = stat[3]
            state = stat[4]
            times = stat[5]
            nodes = stat[6]
            nodelist = stat[7]
            if (state == "R" or state == "PD") and nodelist in instances:
                instances.remove(nodelist)
                
        if instances:
            chosen_instance = random.choice(instances)

        return chosen_instance

    def wait_for_instance(self):
        end = time.time()
        self.log_progress(f"WAITING FOR INSTANCE: SLEEP 10 SECONDS...ELAPSED={round(end-self.start, 2)}s")
        time.sleep(10)

    def show_progress(self, n_pack, submitted_jobs):
        progress = round((submitted_jobs / self.total_jobs) * 100, 2)
        end = time.time()
        self.log_progress(f"{n_pack} JOBS SUBMITTED: ({submitted_jobs}/{self.total_jobs}){progress}%...ELAPSED={round(end-self.start, 2)}s")
        time.sleep(10)
        

    def collect_metrics(self, exe_file, sra_ids, metrics, repeat=1):
        submitted_jobs = 0
        self.total_jobs = len(sra_ids) * len(metrics[0]) * len(metrics[1]) * len(metrics[2]) * repeat
        for n in range(repeat):
            for sra in sra_ids:
                combi = self.generate_packing_combination(metrics)
                for pack_args in combi:
                    instance = self.get_idle_instance()        
                    while instance == None:
                        self.wait_for_instance()
                        instance = self.get_idle_instance()  
                    n_pack = len(pack_args)
                    submitted_jobs += n_pack
                    pack_threads = []
                    for args in pack_args:
                        self.clear_cache(instance)
                        args.insert(0, sra)
                        thread = Thread(target=self.submit_job, args=(exe_file, args, instance, n_pack))
                        pack_threads.append(thread)
                        self.threads.append(thread)
                    self.pack_id += 1
                    for thread in pack_threads:
                        thread.start()
                    self.show_progress(n_pack, submitted_jobs)
        assert submitted_jobs == self.total_jobs, f"TOTAL={self.total_jobs} but SUBMITTED={submitted_jobs}" 
        while len(self.finished_jobs) < self.total_jobs:
            now = time.time()
            self.log_progress(f"Elapsed: {round(now-self.start,2)}s")
            time.sleep(10)
        for thread in self.threads:
            thread.join()
        assert len(self.finished_jobs) == self.total_jobs, f"TOTAL={self.total_jobs} but FINISHED={len(self.finished_jobs)}"
        self.logfile.close()
    
    def clear_cache(self, instance):
        client = self.client_dict[instance]
        command = "sudo sh -c '/usr/bin/echo 3 > /proc/sys/vm/drop_caches' && swapoff -a && swapon -a"
                
        result = client.exec_command(command)
        
    def log_job_packing(self, timestamp, job_id, n_pack):
        self.job_packing_file.write(f"{timestamp},{job_id},{n_pack}\n")

    
        
        
    