import json
import os
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

# Function to check and update device info
def check_devices():
    baseline_file = "device_baseline.json"
    current_info = {
        "CPU": get_cpu_info(),
        "SSD": get_ssd_info(),
        "GPU": get_gpu_info(),
        "RAM": get_ram_info()
    }

    if not os.path.exists(baseline_file):
        with open(baseline_file, "w") as file:
            json.dump(current_info, file)
        return

    with open(baseline_file, "r") as file:
        baseline_info = json.load(file)

    if current_info != baseline_info:
        notification.notify(
            title="Device Change Detected",
            message="One or more of your devices (CPU, SSD, GPU, RAM) have changed.",
            app_name="Device Monitor"
        )

# Run the check
check_devices()
