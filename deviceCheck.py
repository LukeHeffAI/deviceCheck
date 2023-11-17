import json
import os
import sys
import datetime
import platform
import subprocess
from plyer import notification
import psutil
import GPUtil

import smtplib
from email.message import EmailMessage

def check_user_details():
    if not os.path.exists("user_details.json"):
        print("User details not found. Please enter your details.")
        setup_user_details()  # Call the function to set up user details

def setup_user_details():
    user_details = {}
    user_details['full_name'] = input("Enter your full name: ")
    user_details['email'] = input("Enter your email address: ")

    with open("user_details.json", "w") as file:
        json.dump(user_details, file, indent=4)
    
    print("User details saved successfully.")

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
        # Skip loop devices
        if partition.device.startswith('/dev/loop'):
            continue

        if partition.fstype:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                ssd = "SSD" if "SSD" in partition.opts else "HDD"
                ssds.append({"device": partition.device, "total": usage.total, "type": ssd})
            except PermissionError:
                continue
    return ssds

# Function to get GPU info
def get_gpu_info():
    try:
        gpus = GPUtil.getGPUs()
        return [{"name": gpu.name, "id": gpu.id, "serial_number": gpu.serial} for gpu in gpus]  # Assuming GPUtil can provide serial numbers
    except ImportError:
        return ["GPUtil not installed"]

# Function to get RAM info
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

# Function to crop the log file to the last 90 days
def limit_log_file(log_file):
    time_limit = datetime.datetime.now() - datetime.timedelta(days=90)
    with open(log_file, "r") as file:
        lines = file.readlines()

    with open(log_file, "w") as file:
        for line in lines:
            try:
                # Extract the date and time from the log entry
                log_date_str = line.split(": ", 1)[0]  # Split only on the first colon and space
                log_date = datetime.datetime.strptime(log_date_str, "%Y-%m-%d %H:%M:%S")
                if log_date > time_limit:
                    file.write(line)
            except ValueError as e:
                # Handle any parsing errors
                print(f"Error parsing date from log line: {line}. Error: {e}")

def compare_and_notify(current_info, baseline_info):
    try:
        with open("user_details.json", "r") as file:
            user_details = json.load(file)
    except FileNotFoundError:
        user_details = {"full_name": "Unknown User", "email": "no-reply@example.com"}

    changes_detected = False
    for device in current_info.keys():
        if current_info[device] != baseline_info[device]:
            message = f"{device} has changed. Detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            notification.notify(
                title="Device Change Detected",
                message=message,
                app_name="Device Monitor"
            )
            change_details = f"Change detected in {device}"
            log_change(change_details)
            changes_detected = True

    if not changes_detected:
        log_change("No changes detected in devices.")

    # Ensure email is only sent once for a device change, and then reset once conflict resolved
    if changes_detected and not os.path.exists("email_sent.flag"):
        send_email("Device Change Alert for " + user_details.get("full_name", "Unknown User"), 
                   "Changes detected in device configuration.", 
                   ["admin@example.com", "user@example.com"], 
                   user_details)
        open("email_sent.flag", "w").close()  # Create a flag file to indicate email has been sent
    elif not changes_detected and os.path.exists("email_sent.flag"):
        os.remove("email_sent.flag")  # Remove the flag file if no changes are detected

# Function to send an email
def send_email(subject, body, recipient_emails):
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    user_full_name = user_details.get("full_name", "Unknown User")
    user_email = user_details.get("email", "no-reply@example.com")

    body = f"User: {user_full_name}\nEmail: {user_email}\n\n{body}"

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_emails + [user_email]  # Add user's email to the recipient list

    try:
        with smtplib.SMTP_SSL('smtp.example.com', 465) as smtp:  # Replace with your SMTP server details
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_devices():
    baseline_file = "device_baseline.json"
    current_info = {
        "CPU": get_cpu_info(),
        "SSD": get_ssd_info(),
        "GPU": get_gpu_info(),
        "RAM": get_ram_info(),
    }

    reset_baseline = "--reset-baseline" in sys.argv

    if reset_baseline:
        with open(baseline_file, "w") as file:
            json.dump(current_info, file, indent=4, sort_keys=True)
        print("Baseline file reset with current device info.")
        return

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