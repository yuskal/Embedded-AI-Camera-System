import subprocess
import time
import json
import os


system_count = 0
power_files = {
    "Total Power": "/sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power0_input",
    "GPU Power": "/sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power1_input",
    "CPU Power": "/sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power2_input",
}
temperature_files = [
    "/sys/devices/virtual/thermal/thermal_zone0/temp",  # CPU
    "/sys/devices/virtual/thermal/thermal_zone1/temp",  # GPU
    "/sys/devices/virtual/thermal/thermal_zone2/temp",  # AUX
]
gefahr_threshold = 95.0  # Set the danger threshold temperature in Celsius



# Log-System
def log(message):
    global system_count
    try:
        with open('/proc/uptime', 'r') as f:
            TIME = float(f.readline().split()[0])
    except Exception:
        with open('log.txt', 'a') as file:
            file.write(f"{system_count} <<ROOT>> ERROR! CANT ACCESS SYSTEM-TIME!\n")
        TIME = 0
    TIME = round(TIME / 60, 1)
    with open('log.txt', 'a') as file:
        file.write(f"{system_count} <<ROOT>> {message}  *** {TIME} min\n")


# Reads power consumption files
def read_power(file_path):
    try:
        with open(file_path, "r") as file:
            power_microwatts = int(file.read().strip())
            power_watts = power_microwatts / 1_000_000
            return power_watts
    except FileNotFoundError:
        log(f"File {file_path} not found.")
        return None


# SSH per Kabel starten
def enable_adb_reverse():
    os.system("adb start-server")
    os.system("adb reverse tcp:8022 tcp:22")


# Reads temperature sensors
def read_temperature(file_path):
    try:
        with open(file_path, "r") as file:
            temp_millidegrees = int(file.read().strip())
            temp_celsius = temp_millidegrees / 1000
            return temp_celsius
    except FileNotFoundError:
        log(f"Temperature file {file_path} not found.")
        return None


# Checks if any temperature exceeds the threshold and suspends if necessary
def check_and_suspend():
    for temp_path in temperature_files:
        temp = read_temperature(temp_path)
        if temp is not None:
            if temp > gefahr_threshold:
                log(f"TEMPERATURE {temp:.2f} °C EXCEEDS DANGER THRESHOLD! SUSPENDING...")
                try:
                    subprocess.run(['sudo', 'systemctl', 'suspend'], check=True)
                except subprocess.CalledProcessError as e:
                    log(f"Suspend command failed: {e}")
                break



if __name__ == '__main__':
    # Initial sleep
    time.sleep(1)

    # Get system_count from variables.json
    with open('variables.json', 'r') as file:
        variables = json.load(file)
    system_count = variables["system_count"]
    system_count += 1
    variables["system_count"] = system_count
    with open('variables.json', 'w') as file:
        json.dump(variables, file, indent=4)

    log("Root started...")

    # Activate fan using Jetson Clocks
    try:
        subprocess.run(['sudo', '/usr/bin/jetson_clocks'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    log("Jetson Clocks activated")

    # Aktiviere SSH sodass man sich per Kabel verbinden kann
    time.sleep(2)
    try:
        enable_adb_reverse()
        log("SSH activated!")
    except Exception as e:
        print(f"An SSH error occurred: {e}")

    # Main Loop
    try:
        while True:
            # Log power consumption
            for label, path in power_files.items():
                power = read_power(path)
                if power is not None:
                    log(f"{label}: {power:.2f} Watt")
            
            # Check temperatures and suspend if above threshold
            check_and_suspend()
            
            # Sleep for 20 minutes
            time.sleep(1200)
    finally:
        log("Terminating...")





