class Job:
    def __init__(self, job_id, alloc_cpu, alloc_mem, sra_id, pack_id, pid=None, n_pack=1, thread=None):
        # contain pre-completetion data
        self.id = job_id
        self.alloc_cpu = alloc_cpu
        self.alloc_mem = alloc_mem
        self.sra_id = sra_id
        self.pack_id = pack_id
        self.pid = pid
        self.n_pack = n_pack 
        self.thread = thread
    


