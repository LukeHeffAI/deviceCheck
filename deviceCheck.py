import json
import os
import datetime
import platform
import subprocess
from plyer import notification
import psutil

# Function to get CPU info
def get_cpu_info():
    cpu_info = {
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
    }

    # Getting CPU model name using different methods depending on the OS
    if platform.system() == "Windows":
        cpu_info["model_name"] = platform.processor()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo | grep 'model name' | uniq"
        cpu_info["model_name"] = subprocess.check_output(command, shell=True).strip().decode()
    elif platform.system() == "Darwin":  # macOS
        command = "sysctl -n machdep.cpu.brand_string"
        cpu_info["model_name"] = subprocess.check_output(command, shell=True).strip().decode()

    return cpu_info

# Function to get SSD info
def get_ssd_info():
    ssds = []
    for partition in psutil.disk_partitions():
        if partition.fstype:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                ssd = "SSD" if "SSD" in partition.opts else "HDD"
                ssds.append({"device": partition.device, "total": usage.total, "type": ssd})
            except PermissionError:
                # This can happen on some systems
                continue
    return ssds

# Function to get GPU info (same as before)
def get_gpu_info():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        return [gpu.name for gpu in gpus]
    except ImportError:
        return ["GPUtil not installed"]

# Function to get RAM info (same as before)
def get_ram_info():
    try:
        ram = psutil.virtual_memory()
        return f"{ram.total / (1024 ** 3):.2f} GB"
    except ImportError:
        return "psutil not installed"
    
# Function to log changes to a file
def log_change(message):
    log_file = "device_changes.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp}: {message}\n"

    # Create or append to the log file
    with open(log_file, "a") as file:
        file.write(log_entry)

    # Limit log file to last 6 months
    limit_log_file(log_file)

def limit_log_file(log_file):
    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=182)
    with open(log_file, "r") as file:
        lines = file.readlines()

    with open(log_file, "w") as file:
        for line in lines:
            try:
                # Extract and parse the date from the log entry
                log_date = datetime.datetime.strptime(line.split(":")[0], "%Y-%m-%d %H:%M:%S")
                if log_date > six_months_ago:
                    file.write(line)
            except ValueError as e:
                # Handle any parsing errors (e.g., log line not in expected format)
                print(f"Error parsing date from log line: {line}. Error: {e}")

def compare_and_notify(current_info, baseline_info):
    changes_detected = False
    for device in current_info.keys():
        if current_info[device] != baseline_info[device]:
            message = f"{device} has changed. Detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            notification.notify(
                title="Device Change Detected",
                message=message,
                app_name="Device Monitor"
            )
            log_change(f"{device} changed from {baseline_info[device]} to {current_info[device]}")
            changes_detected = True

            # Ask user to confirm if the change is legitimate
            response = input(f"Change detected in {device}. Is this a legitimate change? (y/n): ")
            if response.lower() == 'y':
                baseline_info[device] = current_info[device]

    if not changes_detected:
        log_change("No changes detected in devices.")

def check_devices():
    baseline_file = "device_baseline.json"
    current_info = {
        "CPU": get_cpu_info(),
        "SSD": get_ssd_info(),
        "GPU": get_gpu_info(),
        "RAM": get_ram_info(),
    }

    # Check if the baseline file exists
    if not os.path.exists(baseline_file):
        # If not, create a new baseline file with current info
        with open(baseline_file, "w") as file:
            json.dump(current_info, file, indent=4, sort_keys=True)
        print("Baseline file created. No comparisons to make on first run.")
        return  # Exit the function as there's nothing to compare yet

    # If the baseline file exists, load it and compare
    with open(baseline_file, "r") as file:
        baseline_info = json.load(file)

    compare_and_notify(current_info, baseline_info)

    # Update baseline with current info after user confirmation
    with open(baseline_file, "w") as file:
        json.dump(baseline_info, file, indent=4, sort_keys=True)

# Run the check
check_devices()