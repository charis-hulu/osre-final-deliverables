import os
import time
import sys
import csv

def get_process_info(pid):
    try:
        proc_path = f"/proc/{pid}"
        with open(os.path.join(proc_path, "stat"), 'r') as stat_file:
            stat_data = stat_file.read().split()

        with open(os.path.join(proc_path, "statm"), 'r') as statm_file:
            statm_data = statm_file.read().split()

        with open(os.path.join(proc_path, "io"), 'r') as io_file:
            io_data = io_file.readlines()
        
        with open("/proc/uptime", 'r') as system_file:
            system_data = system_file.read().split()
        
        # Extract relevant information
        CLOCK_TICK= os.sysconf(os.sysconf_names["SC_CLK_TCK"])

        utime_sec = float(stat_data[13]) / CLOCK_TICK
        stime_sec = float(stat_data[14]) / CLOCK_TICK
        starttime_sec = float(stat_data[21]) / CLOCK_TICK
        uptime_sec=float(system_data[0])

        vm_size = int(statm_data[0]) * os.sysconf(os.sysconf_names["SC_PAGE_SIZE"]) 
        rss = int(statm_data[1]) * os.sysconf(os.sysconf_names["SC_PAGE_SIZE"])  
        io_read_bytes = int(io_data[4].split()[1])
        io_write_bytes = int(io_data[5].split()[1])

        # Calculate CPU usage
    
        total_time_sec = utime_sec + stime_sec
        elapsed_sec = uptime_sec - starttime_sec
      
        #print("ELAPSED:", elapsed_sec)
        cpu_percent = 100.0 * (total_time_sec / elapsed_sec)

        return cpu_percent, vm_size, rss, io_read_bytes, io_write_bytes
    
    except FileNotFoundError:
        print(f"Process with PID {pid} not found.")
        sys.exit(1)

if __name__ == "__main__":
    
    
    if len(sys.argv) != 6:
        print("Usage: python script.py <JOB_ID> <PID> <N_PACK> <PACK_ID> <interval>")
        sys.exit(1)

    
    try:
        job_id = int(sys.argv[1])
        pid = int(sys.argv[2])
        n_pack = int(sys.argv[3])
        pack_id = int(sys.argv[4])
        interval = float(sys.argv[5])
        #print(job_id, pid, interval)
        #print(sys.argv[1], sys.argv[2], sys.argv[3])
        

        logfile = open(f"/home/cc/nfs/main/collect_metrics_v2/results/{job_id}_stat.csv", "w")

        fieldnames = ['timestamp', 'job_id', 'pid', 'n_pack', 'pack_id', 'cpu', 'vsz_bytes', 'rss_bytes', 'read_bytes', 'write_bytes']
        writer = csv.DictWriter(logfile, fieldnames=fieldnames)
        writer.writeheader()

        prev_utime_sec = 0
        prev_stime_sec = 0
        prev_elapsed_sec = 0
        prev_uptime_sec = 0
        while True:
            
            try:
                

                proc_path = f"/proc/{pid}"
                with open(os.path.join(proc_path, "stat"), 'r') as stat_file:
                    stat_data = stat_file.read().split()

                with open(os.path.join(proc_path, "statm"), 'r') as statm_file:
                    statm_data = statm_file.read().split()

                with open(os.path.join(proc_path, "io"), 'r') as io_file:
                    io_data = io_file.readlines()
                
                with open("/proc/uptime", 'r') as system_file:
                    system_data = system_file.read().split()
                
                
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Extract relevant information
                CLOCK_TICK= os.sysconf(os.sysconf_names["SC_CLK_TCK"])

                utime_sec = float(stat_data[13]) / CLOCK_TICK
                stime_sec = float(stat_data[14]) / CLOCK_TICK
                starttime_sec = float(stat_data[21]) / CLOCK_TICK
                uptime_sec = float(system_data[0])

                vm_size = int(statm_data[0]) * os.sysconf(os.sysconf_names["SC_PAGE_SIZE"])  # Convert to MB
                rss = int(statm_data[1]) * os.sysconf(os.sysconf_names["SC_PAGE_SIZE"])  # Convert to MB
                io_read_bytes = int(io_data[4].split()[1])
                io_write_bytes = int(io_data[5].split()[1])
                
                # Calculate CPU usage
            
                total_time_sec = (utime_sec - prev_utime_sec) + (stime_sec - prev_stime_sec)
                elapsed_sec = uptime_sec - max(starttime_sec, prev_uptime_sec)
               
                cpu_percent = 100.0 * (total_time_sec / elapsed_sec)

                # print("ELAPSED:", elapsed_sec)
                # print("UTIME:", float(stat_data[13]) / CLOCK_TICK )
                # print("P_UTIME:", prev_utime_sec)
                # print("STIME:", float(stat_data[14]) / CLOCK_TICK )
                # print("P_STIME:", prev_stime_sec)
                
                prev_utime_sec = utime_sec
                prev_stime_sec = stime_sec
                prev_uptime_sec = uptime_sec

                
                writer.writerow({
                    'timestamp': current_time,
                    'job_id': job_id,
                    'pid': pid,
                    'n_pack': n_pack,
                    'pack_id': pack_id,
                    'cpu': f"{cpu_percent:.4f}",
                    'vsz_bytes': vm_size,
                    'rss_bytes': rss,
                    'read_bytes': io_read_bytes,
                    'write_bytes': io_write_bytes
                }
                )

               # print(prev_uptime_sec)
          
            except FileNotFoundError:
                print(f"Process with PID {pid} not found.")
                logfile.close()
                sys.exit(1)
            #cpu_percent, vm_size, rss, io_read_bytes, io_write_bytes = get_process_info(pid)
            #print(f"PID: {pid}, CPU: {cpu_percent:.2f}%, VM Size: {vm_size:.2f} MB, RSS: {rss:.2f} MB, IO Read: {io_read_bytes}, IO Write: {io_write_bytes}")
            time.sleep(interval)
        
    except ValueError:
        print("Error: PID must be an integer and interval must be a float.")
        sys.exit(1)
