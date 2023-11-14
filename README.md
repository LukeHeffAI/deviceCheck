# Device Change Detection Script

## Overview
This script monitors your computer's hardware (CPU, SSD, GPU, and RAM) and notifies you of any changes. It's designed to help maintain the integrity of your computer's hardware.

## Prerequisites
- **Python**: Python must be installed on your system. You can download it from [python.org](https://www.python.org/).
- **Dependencies**: This script uses `psutil`, `GPUtil`, and `plyer`. These libraries need to be installed via pip.

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/). Make sure to add Python to your PATH during installation.

### Step 2: Download the Script
Download `device_monitor.py` from our shared drive and place it in a directory on your computer.

### Step 3: Install Dependencies
Open a terminal (Command Prompt or PowerShell on Windows, Terminal on MacOS/Linux) and execute the following command:

```bash
    pip install psutil GPUtil plyer
```

## Usage

### Running the Script Manually
To run the script manually, follow these steps:

1. Open a terminal.
   - On Windows, you can use Command Prompt or PowerShell.
   - On MacOS or Linux, use the Terminal application.
2. Navigate to the directory where `device_monitor.py` is located. You can use the `cd` command followed by the path to the directory. For example:

```bash
   cd path/to/directory
```
3. Execute the script by running:

```bash
   python device_monitor.py
```

This will compare your current hardware configuration against the baseline. If it's the first run, the script will create a baseline for future comparisons.

Remember to add your log and device details to your ignore file.

### Scheduling the Script

#### Unix-like Systems (MacOS/Linux):
To schedule the script to run hourly:

1. Open a terminal.
2. Type `crontab -e` and press Enter to edit the crontab.
3. Add the following line:
```bash
0 * * * * /usr/bin/python /path/to/device_monitor.py
```
Replace `/usr/bin/python` with the path to your Python executable and `/path/to/device_monitor.py` with the full path to the script.

4. Save and exit the editor. The script will now run automatically every hour.

#### Windows:
To schedule the script using Task Scheduler:

1. Open Task Scheduler.
2. Create a new task with the following settings:
- **Trigger**: Choose to run the task hourly.
- **Action**: Set to 'Start a program'.
- **Program/script**: Enter the path to your Python executable.
- **Add arguments**: Enter the path to `device_monitor.py`.
- **Start in**: Specify the directory where `device_monitor.py` is located.
3. Save the task. The script will now execute at the specified hourly interval.

### Notifications
When the script detects a change in hardware, it will display a notification on your computer. Make sure your system notifications are enabled to receive these alerts.
