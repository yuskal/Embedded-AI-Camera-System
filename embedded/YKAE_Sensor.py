import os
import time
import json

system_count = 0

# Function to read temperature
def get_temperatures():
    base_path = '/sys/class/thermal/'
    temperatures = {}

    # Iterate over thermal zones
    for entry in os.listdir(base_path):
        temp_path = os.path.join(base_path, entry, 'temp')
        type_path = os.path.join(base_path, entry, 'type')
        
        if os.path.isfile(temp_path) and os.path.isfile(type_path):
            try:
                # Read temperature value
                with open(temp_path, 'r') as f:
                    temp_value = int(f.read()) / 1000  # Convert to Celsius
                
                # Read sensor type
                with open(type_path, 'r') as f:
                    sensor_type = f.read().strip()
                
                temperatures[sensor_type] = temp_value
            except (FileNotFoundError, ValueError):
                pass  # Ignore if files are missing or unreadable

    return temperatures

if __name__ == '__main__':
    # Load system count from variables.json
    with open('variables.json', 'r') as file:
        variables = json.load(file)
    system_count = variables["system_count"]

    # Main loop
    try:
        while True:
            temperatures = get_temperatures()
            for sensor, temp in temperatures.items():
                with open('log.txt', 'a') as file:
                    file.write(f"{system_count} <<SENSOR>> {sensor}: {temp} Celsius\n")
            time.sleep(1200)
    finally:
        with open('log.txt', 'a') as file:
            file.write(f"{system_count} <<SENSOR>> Terminiere...\n")

