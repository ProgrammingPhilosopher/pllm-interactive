import os
import shutil
import yaml
import csv

def is_yaml_file(filename):
    return filename.endswith(('.yaml', '.yml'))

def load_yaml_file(filepath):
    with open(filepath, 'r') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            if not 'snippet.py' in filepath: print(f"Error loading YAML file {filepath}: {e}")
            return None

def validate_yaml(data):
    # Example validation: Check if specific keys exist
    required_keys = ["key1", "key2"]
    for key in required_keys:
        if key not in data:
            print(f"Validation error: Missing key '{key}'")
            return False
    return True

def find_and_validate_yaml_file(file):
    # filepath = os.path.join(file)
    # print(filepath)
    if is_yaml_file(file):
        # print(f"Loading YAML file: {filepath}")
        data = load_yaml_file(file)
        if data:
            # print(f"Validating YAML file: {file}")

            iterations = data['iterations']

            if iterations:
                if len(iterations) < 10:
                    print(f"Test successful: {file}")
                    current_result = True

def delete_all_files(directory, filename_to_keep='snippet.py'):
        # List all files in the directory
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)

        # Check if it is the file to keep
        if item == filename_to_keep:
            print(f"Kept {item_path}")
            continue
        
        # Delete directories
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Deleted directory {item_path}")
        
        # Delete files
        elif os.path.isfile(item_path):
            os.remove(item_path)
            print(f"Deleted file {item_path}")

def write_array_to_file(array, file_path):
    try:
        # Delete the file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted existing file: {file_path}")

        # Open the file in write mode and write each element to a new line
        with open(file_path, 'w') as file:
            for path in array:
                paths = path.split('/')
                file.write(f"/code/{paths[-2]}/{paths[-1]}\n")
                print(f"Written to file: '/code/{paths[-2]}/{paths[-1]}'")
    except Exception as e:
        print(f"Error: {e}")

def find_and_validate_yaml_files(directory):
    total = 0 # Starts at negative 1 to negate the first folder in the list
    success = 0
    failed = 0
    
    error_types = {
        'NoMatchingDistribution': 0,
        'InvalidRequirement': 0,
        'CouldNotBuildWheels': 0,
        'ImportError': 0,
        'ModuleNotFound': 0,
        'AttributeError': 0,
        'SyntaxError': 0,
        'OtherFailure': 0,
        'OtherPass': 0,
        'DjangoPass': 0,
        'NameError': 0,
        'TypeError': 0,
        'FailedToRun': 0
    }

    failed_to_run = []
    import_error = []
    module_not_found = []
    syntax_error = []
    all_types = []
    
    current_root = ''
    # current_result = False # False until proven successful

    for root, dirs, files in os.walk(directory):
        if not '/modules' in root and len(files) > 0:

            # if total == 100: break # Escape to save from running all results
            # print(total)

            current_result = {'result': '', 'value': -1}
            
            for file in files:
                filepath = os.path.join(root, file)
                # print(filepath)
                if is_yaml_file(file):
                    filepath = os.path.join(root, file)
                    # print(f"Loading YAML file: {filepath}")
                    data = load_yaml_file(filepath)
                    if data:
                        # print(f"Validating YAML file: {filepath}")
                        iterations = data['iterations']

                        if iterations:
                            if len(iterations) < 10:
                                # print(f"Test successful: {filepath}")
                                final_error = iterations[f"iteration_{len(iterations)}"][2]['error']
                                final_error_type = iterations[f"iteration_{len(iterations)}"][1]['error_type']
                                # current_result = True
                                    
                                if 'ModuleNotFound' in final_error:
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'ModuleNotFound', 'value': 1}
                                elif 'ImportError' in final_error:
                                    if 'variable DJANGO_SETTINGS_MODULE is undefined' in final_error:
                                        if current_result['value'] < 4:
                                            current_result = {'name': root, 'file': file, 'result': 'DjangoPass', 'value': 4}
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'ImportError', 'value': 1}
                                elif 'No matching distribution' in final_error:
                                    # print('No matching distribution')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'NoMatchingDistribution', 'value': 1}
                                elif 'Could not build wheels' in final_error or 'Failed building wheel' in final_error:
                                    # print('Could not build wheels')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'CouldNotBuildWheels', 'value': 1}
                                elif 'Invalid requirement' in final_error:
                                    # print('Invalid requirement')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'InvalidRequirement', 'value': 1}
                                elif 'failed with error code 1' in final_error or 'exit status 1' in final_error or 'problem confirming the ssl certificate' in final_error:
                                    # print('Other')
                                    # print(f"Error code error: {final_error}")
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'OtherFailure', 'value': 1}
                                elif final_error_type == 'NonZeroCode':
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'OtherFailure', 'value': 1}
                                elif 'AttributeError' in final_error:
                                    # print('AttributeError')
                                    if current_result['value'] < 3:
                                        current_result = {'name': root, 'file': file, 'result': 'AttributeError', 'value': 3}
                                elif 'NameError' in final_error:
                                    # print('AttributeError')
                                    if current_result['value'] < 4:
                                        current_result = {'name': root, 'file': file, 'result': 'NameError', 'value': 4}
                                elif 'TypeError' in final_error:
                                    if current_result['value'] < 4:
                                        current_result = {'name': root, 'file': file, 'result': 'TypeError', 'value': 4}
                                elif 'SyntaxError' in final_error:
                                    # print('SyntaxError')
                                    if current_result['value'] < 3:
                                        current_result = {'name': root, 'file': file, 'result': 'SyntaxError', 'value': 3}
                                elif current_result['value'] < 5:
                                    current_result = {'name': root, 'file': file, 'result': 'OtherPass', 'value': 5}
                            else:
                                final_error = ""
                                final_error_type = ""
                                
                                for i in reversed(range(1, len(iterations)+1)):
                                    if final_error == "" and i > 0:
                                        final_error = iterations[f"iteration_{i}"][2]['error']
                                        final_error_type = iterations[f"iteration_{i}"][1]['error_type']


                                if 'ModuleNotFound' in final_error:
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'ModuleNotFound', 'value': 1}
                                elif 'ImportError' in final_error:
                                    if 'variable DJANGO_SETTINGS_MODULE is undefined' in final_error:
                                        if current_result['value'] < 4:
                                            current_result = {'name': root, 'file': file, 'result': 'DjangoPass', 'value': 4}
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'ImportError', 'value': 1}
                                elif 'No matching distribution' in final_error:
                                    # print('No matching distribution')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'NoMatchingDistribution', 'value': 1}
                                elif 'Could not build wheels' in final_error or 'Failed building wheel' in final_error:
                                    # print('Could not build wheels')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'CouldNotBuildWheels', 'value': 1}
                                elif 'Invalid requirement' in final_error:
                                    # print('Invalid requirement')
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'InvalidRequirement', 'value': 1}
                                elif 'failed with error code 1' in final_error or 'exit status 1' in final_error or 'problem confirming the ssl certificate' in final_error:
                                    # print('Other')
                                    # print(f"Error code error: {final_error}")
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'OtherFailure', 'value': 1}
                                elif final_error_type == 'NonZeroCode':
                                    if current_result['value'] < 1:
                                        current_result = {'name': root, 'file': file, 'result': 'OtherFailure', 'value': 1}
                                elif 'AttributeError' in final_error:
                                    # print('AttributeError')
                                    if current_result['value'] < 3:
                                        current_result = {'name': root, 'file': file, 'result': 'AttributeError', 'value': 3}
                                if 'TypeError' in final_error:
                                        if current_result['value'] < 4:
                                            current_result = {'name': root, 'file': file, 'result': 'TypeError', 'value': 4}
                                elif 'NameError' in final_error:
                                    # print('AttributeError')
                                    if current_result['value'] < 4:
                                        current_result = {'name': root, 'file': file, 'result': 'NameError', 'value': 4}
                                elif 'SyntaxError' in final_error:
                                        # print('SyntaxError')
                                    if current_result['value'] < 3:
                                        current_result = {'name': root, 'file': file, 'result': 'SyntaxError', 'value': 3}
                                else:
                                    pass
                    else:
                        if current_result['value'] < 0:
                            current_result = {'name': root, 'file': file, 'result': 'FailedToRun', 'value': 0}
                                # pass
                        # else:
                            # print(f"Test failed: {iterations['iteration_10']}")
                        # if validate_yaml(data):
                        #     print(f"YAML file {filepath} is valid.")
                        # else:
                        #     print(f"YAML file {filepath} is invalid.")
            
            if current_result['result'] == '' or current_result['value'] == 0:
                current_result = {'name': root, 'file': file, 'result': 'FailedToRun', 'value': 0}
                failed_to_run.append(root)

            if current_result['result'] == 'ImportError':
                import_error.append(root)

            if current_result['result'] == 'SyntaxError':
                syntax_error.append(root)

            if current_result['result'] == 'ModuleNotFound':
                module_not_found.append(root)

            error_types[current_result['result']] += 1

            # Load the file which had the end result
            data = load_yaml_file(current_result['name'] + '/' + current_result['file'])
            total_time = 1200
            if data != None:
                total_time = data['total_time'] if 'total_time' in data else 1200
            # print("{:.2f}".format(data['total_time'] / 60))
            # print(f"{}")
            
            
            file_name = current_result['name'].split('/')[-1]
            docker_file = f"Dockerfile-llm-{current_result['file'].split('_')[-1].replace('.yml', '')}"
            
            # print(f"{root}/{docker_file}")

            python_modules = ""

            if current_result['file'] != "snippet.py":
                # Open the Dockerfile in read mode
                with open(f"{root}/{docker_file}", 'r') as file:
                    # Read and process each line
                    for line_number, line in enumerate(file, start=1):
                        # Print the line number and content (optional)
                        if "pip" in line and "install" in line and not "--upgrade" in line:
                            stripped_line = line.split(",")[-1].replace('"', '').split('==')[0]
                            python_modules = f"{python_modules};{stripped_line}" if python_modules != "" else stripped_line
                            
                        # print(f"Line {line_number}: {line.strip()}")

            # if current_result['value'] < 4:
            #     print(f"FAILED  {file_name}: {current_result['result']}")

            all_types.append({'id': '10', 'name': file_name, 'file': current_result['file'], 'result': current_result['result'], 'python_modules': python_modules, 'duration': round(total_time, 2), 'passed': True if current_result['value'] >= 4 else False})
            
            total += 1
        
        else:
            if not '/modules' in root:
                print(root)
    
    # print(failed_to_run)
    
    # for path in module_not_found:
    #     paths = path.split('/')
    #     print(f"/code/{paths[-2]}/{paths[-1]}")

    # for path in import_error:
    #     paths = path.split('/')
    #     print(f"/code/{paths[-2]}/{paths[-1]}")

    # for path in syntax_error:
    #     paths = path.split('/')
    #     print(f"/code/{paths[-2]}/{paths[-1]}")

    # for path in failed_to_run:
    #     paths = path.split('/')
    #     print(f"/code/{paths[-2]}/{paths[-1]}")
    
    # write_array_to_file(failed_to_run, './re_run.csv')
    # write_array_to_file(module_not_found + import_error + failed_to_run, './re_run.csv')

    # print(len(all_types))
    # for item in all_types:
    #     print(item)

    # Writing to a CSV file
    
    with open('./../pllm_results/hard-gists-l10-r1-10-final.csv', 'w', newline='') as csvfile:
        # Get the column headers from the first dictionary
        fieldnames = all_types[0].keys()
    
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
        writer.writeheader()  # Write the header (keys)
    
        for row in all_types:
            writer.writerow(row)

    print(f"{error_types['OtherPass']+error_types['DjangoPass']+error_types['NameError']+error_types['TypeError']} out of {total} passed!")
    print(error_types)

# Replace 'your_directory' with the path to the directory you want to search
find_and_validate_yaml_files(f'./hard-gists-l10-r1-10')

# FULL TEST RUNS
r1_1 = "1437 out of 2891 passed!"
r1_1 = {'NoMatchingDistribution': 282, 'InvalidRequirement': 17, 'CouldNotBuildWheels': 83, 'ImportError': 433, 'ModuleNotFound': 8, 'AttributeError': 83, 'SyntaxError': 494, 'OtherFailure': 45, 'OtherPass': 1269, 'DjangoPass': 26, 'NameError': 68, 'TypeError': 74, 'FailedToRun': 9}

r1_2 = "1419 out of 2891 passed!"
r1_2 = {'NoMatchingDistribution': 276, 'InvalidRequirement': 20, 'CouldNotBuildWheels': 70, 'ImportError': 457, 'ModuleNotFound': 13, 'AttributeError': 77, 'SyntaxError': 505, 'OtherFailure': 49, 'OtherPass': 1249, 'DjangoPass': 26, 'NameError': 71, 'TypeError': 73, 'FailedToRun': 5}

r1_3 = "1424 out of 2891 passed!"
r1_3 = {'NoMatchingDistribution': 272, 'InvalidRequirement': 15, 'CouldNotBuildWheels': 68, 'ImportError': 469, 'ModuleNotFound': 9, 'AttributeError': 70, 'SyntaxError': 503, 'OtherFailure': 56, 'OtherPass': 1252, 'DjangoPass': 25, 'NameError': 69, 'TypeError': 78, 'FailedToRun': 5}

r1_4 = "1416 out of 2891 passed!"
r1_4 = {'NoMatchingDistribution': 285, 'InvalidRequirement': 24, 'CouldNotBuildWheels': 81, 'ImportError': 430, 'ModuleNotFound': 13, 'AttributeError': 79, 'SyntaxError': 501, 'OtherFailure': 55, 'OtherPass': 1248, 'DjangoPass': 33, 'NameError': 64, 'TypeError': 71, 'FailedToRun': 7}

r1_5 = "1434 out of 2891 passed!"
r1_5 = {'NoMatchingDistribution': 211, 'InvalidRequirement': 21, 'CouldNotBuildWheels': 62, 'ImportError': 499, 'ModuleNotFound': 10, 'AttributeError': 70, 'SyntaxError': 512, 'OtherFailure': 66, 'OtherPass': 1261, 'DjangoPass': 28, 'NameError': 70, 'TypeError': 75, 'FailedToRun': 6}

r1_6 = "1418 out of 2891 passed!"
r1_6 = {'NoMatchingDistribution': 223, 'InvalidRequirement': 21, 'CouldNotBuildWheels': 70, 'ImportError': 520, 'ModuleNotFound': 8, 'AttributeError': 68, 'SyntaxError': 481, 'OtherFailure': 44, 'OtherPass': 1240, 'DjangoPass': 31, 'NameError': 71, 'TypeError': 76, 'FailedToRun': 38}

r1_7 = "1422 out of 2891 passed!"
r1_7 = {'NoMatchingDistribution': 237, 'InvalidRequirement': 16, 'CouldNotBuildWheels': 68, 'ImportError': 500, 'ModuleNotFound': 8, 'AttributeError': 68, 'SyntaxError': 511, 'OtherFailure': 54, 'OtherPass': 1247, 'DjangoPass': 28, 'NameError': 70, 'TypeError': 77, 'FailedToRun': 7}

r1_8 = "1414 out of 2891 passed!"
r1_8 = {'NoMatchingDistribution': 220, 'InvalidRequirement': 26, 'CouldNotBuildWheels': 59, 'ImportError': 505, 'ModuleNotFound': 15, 'AttributeError': 83, 'SyntaxError': 472, 'OtherFailure': 61, 'OtherPass': 1244, 'DjangoPass': 27, 'NameError': 69, 'TypeError': 74, 'FailedToRun': 36}

r1_9 = "1421 out of 2891 passed!"
r1_9 = {'NoMatchingDistribution': 229, 'InvalidRequirement': 26, 'CouldNotBuildWheels': 68, 'ImportError': 500, 'ModuleNotFound': 11, 'AttributeError': 79, 'SyntaxError': 487, 'OtherFailure': 64, 'OtherPass': 1254, 'DjangoPass': 29, 'NameError': 62, 'TypeError': 76, 'FailedToRun': 6}

r1_10 = "1420 out of 2891 passed!"
r1_10 = {'NoMatchingDistribution': 248, 'InvalidRequirement': 20, 'CouldNotBuildWheels': 66, 'ImportError': 520, 'ModuleNotFound': 10, 'AttributeError': 75, 'SyntaxError': 470, 'OtherFailure': 56, 'OtherPass': 1244, 'DjangoPass': 31, 'NameError': 72, 'TypeError': 73, 'FailedToRun': 6}

new_gist_1 = "127 out of 372 passed!"
new_gist_1 = {'NoMatchingDistribution': 26, 'InvalidRequirement': 1, 'CouldNotBuildWheels': 2, 'ImportError': 25, 'ModuleNotFound': 1, 'AttributeError': 1, 'SyntaxError': 29, 'OtherFailure': 2, 'OtherPass': 115, 'DjangoPass': 0, 'NameError': 2, 'TypeError': 10, 'FailedToRun': 158}
