
from datetime import datetime
import os

def parse_error_message(state, message):
    if 'ModuleNotFound' in message:
        return 'ModuleNotFound'
    elif 'ImportError' in message:
        return 'ImportError'
    elif 'No matching distribution' in message:
        return 'NoMatchingDistribution'
    elif 'Could not build wheels' in message or 'Failed building wheel' in message:
        return 'CouldNotBuildWheels'
    elif 'Invalid requirement' in message:
        return 'InvalidRequirement'                        
    elif 'AttributeError' in message:
        return 'AttributeError'
    elif 'NameError' in message:
        return 'NameError'
    elif 'TypeError' in message:
        return 'TypeError'
    elif 'SyntaxError' in message:
        return 'SyntaxError'
    # elif 'failed with error code 1' in message or 'exit status 1' in message or 'problem confirming the ssl certificate' in message:
    #     print(f"Error code error: {state} | {message}")
    #     return 'OtherFailure'
    else:
        if 'Success' in state:
            return 'OtherPass'
        else:
            return 'OtherFailure'

def parse_log_file(file):

    error_types = {
        'NoMatchingDistribution': 0,
        'InvalidRequirement': 0,
        'CouldNotBuildWheels': 0,
        'ImportError': 0,
        'ModuleNotFound': 0,
        'OtherFailure': 0,
        'OtherPass': 0,
        'NameError': 0,
        'AttributeError': 0,
        'SyntaxError': 0,
        'TypeError': 0,
        'FailedToRun': 0
    }

    results = []
    previous_message = ""
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    start_time = ""
    previous_result = ""

    with open(file, 'r') as file:
        log_lines = file.readlines()

    for line in log_lines:
        # Example log line: "2024-08-19 12:34:56,789 INFO Some message here"
        parts = line.split(' ')  # Split by space
        timestamp = parts[0] + ' ' + parts[1]  # Combine date and time
        log_level = parts[2]  # Log level (e.g., INFO)
        message = ' '.join(parts[3:])  # The rest is the message

        # We need to store the start of the run
        if "---START---" in line:
            start_time = datetime.strptime(timestamp, time_format)
        if '<proc' in message:
            message_parts = message.replace('\n', '').replace(' ', '').split('>')[1].split(':')
            state = message_parts[1]
            name = message_parts[0]
            error = parse_error_message(state, previous_message)

            error_types[error] += 1

            # Calculate the total run-time based on the previously stored time
            dt2 = datetime.strptime(timestamp, time_format)
            total_time = (dt2 - start_time).total_seconds()
            
            python_modules = ""
            apt_installs = 0
            dockerfile_path = f"./../pyego-results/hard-gists/{name}/Dockerfile"
            if os.path.isfile(dockerfile_path):
            # print(f"./../pyego-results/hard-gists/{name}/Dockerfile")
                with open(dockerfile_path, 'r') as file:
                    # Read and process each line
                    for line_number, line in enumerate(file, start=1):
                        # Print the line number and content (optional)
                        # print(f"Line {line_number}: {line.strip()}")
                        if "pip" in line and "install" in line and not "--upgrade" in line and not 'python-pip' in line:
                            stripped_line = line.split(",")[-1].replace('"', '').split('==')[0]
                            stripped_line = line.split(" ")[-1].split('==')[0]
                            python_modules = f"{python_modules};{stripped_line}" if python_modules != "" else stripped_line
                        
                        if 'apt-get' in line and 'install' in line and not "--upgrade" in line and not 'python-pip' in line:
                            apt_installs += 1
            # else:
                # print(f"{name}: No Dockerfile")
                # print({'id': '1', 'name': name, 'result': error, 'duration': round(total_time, 2), 'python_modules': python_modules, 'total_modules': len(python_modules.split(';')), 'apt_installs': apt_installs, 'passed': True if state == 'Success' else False})
                            
            # print({'id': '1', 'name': name, 'result': error, 'duration': round(total_time, 2), 'python_modules': python_modules, 'total_modules': len(python_modules.split(';')), 'apt_installs': apt_installs, 'passed': True if state == 'Success' else False})
            results.append({'id': '1', 'name': name, 'result': error, 'duration': round(total_time, 2), 'python_modules': python_modules, 'total_modules': 0 if python_modules == "" else len(python_modules.split(';')), 'apt_installs': apt_installs, 'passed': True if state == 'Success' else False})
            # print(f"Timestamp: {round(total_time, 2)}, Level: {log_level}, State: {state}, Error: {error}")

            # Set the start time as the current line time.
            start_time = dt2
            # print(previous_message)
            # results.append(message)
        
        previous_message = message

    print(error_types)
    return results

results = parse_log_file("./../pyego-results/hard_gists_test.20240726.log")

for item in results:
    print(item)

print(len(results))

import csv

with open('./../pyego-results/pyego_results_total.csv', 'w', newline='') as csvfile:
        # Get the column headers from the first dictionary
        fieldnames = results[0].keys()
    
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
        writer.writeheader()  # Write the header (keys)
    
        for row in results:
            writer.writerow(row)
            