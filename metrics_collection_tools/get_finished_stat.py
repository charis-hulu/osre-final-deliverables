import os
import subprocess

def find_lowest_job_id(directory_path):
    lowest_number = float('inf')  # A large number to ensure it gets updated by the first file
    #lowest_file = None

    for filename in os.listdir(directory_path):
        if filename.endswith('.out'):
            try:
                number = int(filename[:-4])  # Remove the '.out' extension and convert to integer
                if number < lowest_number:
                    lowest_number = number
                    #lowest_file = os.path.join(directory_path, filename)
            except ValueError:
                # Skip files that do not have a valid number format
                pass

    return lowest_number

def find_highest_job_id(directory_path):
    highest_number = float('-inf')  # A small number to ensure it gets updated by the first file
    #highest_file = None

    for filename in os.listdir(directory_path):
        if filename.endswith('.out'):
            try:
                number = int(filename[:-4])  # Remove the '.out' extension and convert to integer
                if number > highest_number:
                    highest_number = number
                    #highest_file = os.path.join(directory_path, filename)
            except ValueError:
                # Skip files that do not have a valid number format
                pass

    return highest_number

def get_stat_from_sacct(start_id, end_id, logpath):
    logfile = open(logpath, "w")
    for j_id in range(start_id, end_id+1):
        command = f"sacct -j {j_id} --format='all' -P"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = [line for line in result.stdout.split("\n")[1:] if line != ""]
    
        for line in output:
            logfile.write(line)
            logfile.write("\n")
    logfile.close()

if __name__ == "__main__":
    DIR = "/home/cc/nfs/main/collect_metrics_v2"
    LOGPATH = f"{DIR}/sacct.txt"
    
    highest_id = find_highest_job_id(DIR)
    lowest_id = find_lowest_job_id(DIR)

    get_stat_from_sacct(lowest_id, highest_id, LOGPATH)