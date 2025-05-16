
from datetime import datetime
import os
import csv

def parse_error_message(message):
    if 'ModuleNotFound' in message or 'DependencyNotInstalled' in message:
        return 'ModuleNotFound'
    elif 'ImportError' in message:
        return 'ImportError'
    elif 'No matching distribution' in message or 'DistributionNotFound' in message:
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
    elif 'SyntaxError' in message or 'SyntaxWarning' in message:
        return 'SyntaxError'
    elif message == '':
        return 'OtherPass'
    elif 'snippet.py: error' in message or 'FileNotFoundError' in message or 'Python 2 is no longer supported' in message or 'IOError' in message:
        return 'OtherPass'
    elif 'IndexError' in message or 'UserWarning' in message or 'ValueError' in message or 'EOFError' in message or 'django.core.exceptions' in message:
        return 'OtherPass'
    elif 'Requires the full path to a file' in message or 'ImproperlyConfigured' in message or 'DatabaseError' in message or 'DeprecationWarning' in message:
        return 'OtherPass'
    elif 'MySQLInterfaceError' in message or 'UnparsedFlagAccessError' in message or 'TabError' in message or 'OSError' in message or 'TclError' in message:
        return 'OtherPass'
    elif 'NoBackendError' in message or 'MySQLdb' in message or 'AssertionError' in message or 'meowexception' in message or 'WARNING:tensorflow' in message:
        return 'OtherPass'
    elif 'redis.exceptions' in message or 'ConnectionRefusedError' in message or 'FeatureNotFound' in message or 'urllib.error' in message:
        return 'OtherPass'
    elif 'git.exc' in message or 'RuntimeError' in message or 'DJANGO_PROJECT_PATH' in message or 'pygame.error' in message or 'smi.error' in message or 'Using TensorFlow backend' in message:
        return 'OtherPass'
    elif 'ZeroDivisionError' in message or 'KeyError' in message or 'pymongo.errors' in message or 'JAVA_HOME' in message or 'cv2.error' in message or 'infinite attractor' in message:
        return 'OtherPass'
    elif 'ansible.errors' in message or 'tensorflow/stream_executor' in message or 'OAuthException' in message or 'socket.error' in message or 'GITHUB_TOKEN' in message:
        return 'OtherPass'
    elif 'Usage: /app/snippet.py' in message or 'usage: /app/snippet.py' in message or 'usage: snippet.py' in message or 'theano.tensor.blas' in message or 'sqlite3' in message:
        return 'OtherPass'
    elif 'TelegramError' in message or 'reddit-like system' in message or 'JSONDecodeError' in message or 'LookupError' in message or 'ParseError' in message or 'gaierror' in message:
        return 'OtherPass'
    elif 'ReadError' in message or 'APIError' in message:
        return 'OtherPass'
    else:
        return 'OtherPass'

def get_timings():
    gists = {}

    with open('./../readpy-new-results/run_log.txt', 'r') as file:
        output_lines = file.readlines()

    for line in output_lines:
        details = line.replace('\n', '').split(':')
        gist_id = details[0].split('/')[-1]
        date_format = "%Y-%m-%d %H:%M:%S"
        start_time = datetime.strptime(f"{details[1]}:{details[2]}:{details[3]}", date_format)
        end_time = datetime.strptime(f"{details[4]}:{details[5]}:{details[6]}", date_format)
        
        runtime = (end_time - start_time).total_seconds()
        gists[gist_id] = runtime
    
    return gists

def get_pip_install(path):
    python_modules = ""
    dockerfile_path = os.path.join(path, 'Dockerfile')
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
    
    return python_modules
                        
def validate_readpy_results(root_dir="./../readpy-new-results/test-gists"):
    gist_timings = get_timings()

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

    snippet_info = []
    docker_build_failure = []
    total_error = []
    # Loop through each directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check if 'output.txt' exists in the current directory
        if 'output.txt' in filenames:
            directory_id = dirpath.split('/')[-1]
            # Path to the existing output.txt file
            output_file_path = os.path.join(dirpath, 'output.txt')
        
            output_lines = ""
            execution_time = ""
            # Open and read the output.txt file
            with open(output_file_path, 'r') as file:
                execution_time = file.readline()
                output_lines = file.readlines()
            
            output_lines = ' '.join(output_lines)
            find_time = gist_timings[directory_id]
            execution_time = float(execution_time.split(': ')[1]) + find_time
            python_modules = get_pip_install(dirpath)

            if "Dockerfile failed to build" in output_lines:
                docker_build_failure.append(directory_id)
                snippet_info.append({'id': '1', 'name': directory_id, 'result': "Build failure", 'duration': round(execution_time, 2), 'python_modules': python_modules, 'total_modules': 0 if python_modules == "" else len(python_modules.split(';')), 'passed': False})
            else:
                error = parse_error_message(output_lines)
                error_types[error] += 1
                pass_types = 'OtherPass NameError TypeError'
                pass_fail = True if error in pass_types else False
                snippet_info.append({'id': '1', 'name': directory_id, 'result': error, 'duration': round(execution_time, 2), 'python_modules': python_modules, 'total_modules': 0 if python_modules == "" else len(python_modules.split(';')), 'passed': pass_fail})

    # print(snippet_info)
    total = 0
    for obj in error_types:
        total += error_types[obj]

    print(f"{error_types['OtherPass']+error_types['NameError']+error_types['TypeError']} out of {total} passed!")
    print(error_types)
    return snippet_info



snippet_info = validate_readpy_results()

with open('./../readpy-new-results/readpy_results_total.csv', 'w', newline='') as csvfile:
        # Get the column headers from the first dictionary
        fieldnames = snippet_info[0].keys()
    
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
        writer.writeheader()  # Write the header (keys)
    
        for row in snippet_info:
            writer.writerow(row)

# # print(len(build_failure))
# print(len(total_error))
# print(error_types)
# total_pass = error_types['OtherPass']+error_types['NameError']+error_types['AttributeError']+error_types['SyntaxError']+error_types['TypeError']
# total_fail = error_types['NoMatchingDistribution']+error_types['InvalidRequirement']+error_types['CouldNotBuildWheels']+error_types['ImportError']+error_types['ModuleNotFound']+error_types['OtherFailure']
# print(f"Pass: {total_pass}")
# print(f"Failure: {total_fail + len(build_failure)}")
