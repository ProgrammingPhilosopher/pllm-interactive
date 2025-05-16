import os

def merge_arrays(arr1, arr2):
    """
    Merge two lists of values, ensuring uniqueness and overwriting duplicates.

    :param arr1: First list of values.
    :param arr2: Second list of values.
    :return: Merged list of unique values.
    """
    merged_set = set(arr1)  # Convert first array to a set to ensure uniqueness
    merged_set.update(arr2)  # Add all elements from the second array, overwriting duplicates

    return list(merged_set)

def filter_module(module):
    from helpers.py_pi_query import PyPIQuery
    pypi = PyPIQuery()

    query = pypi.query_module(module)
    
    if not query:
        print(f"{module} = False")
    else:
        print(f"{module} = True")

    return query

def process_yaml_files(root_folder):
    modules_list = []
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                file_path = os.path.join(subdir, file)
                modules_list = merge_arrays(modules_list, process_file(file_path))
    
    print(modules_list)
    print('\n')

    end_modules = []

    for module in modules_list:
        out = filter_module(module)
        if not out:
            end_modules.append(module)

def ensure_8_spaces(line):
    if not line.startswith(' ' * 8):
        return ' ' * 8 + line.lstrip()
    return line

def process_file(file_path):
    modules = []
    with open(file_path, 'r') as f:
        lines = f.readlines()

    modified = False
    for i in range(len(lines)):
        # if 'No matching distribution found for' in lines[i]:
            # if 'obelISK' in lines[i]:
            #     print(file_path)


            # print(file_path)
            # for i, line in enumerate(lines[i].split(' ')):
            #     if '==' in line:
            #         module = line.split('==')[0]
            #         if not module in modules:
            #             modules.append(module)




            # print(lines[i].split(' '))
            # print('\n')
        # print(lines[i])
        if '^' in lines[i] and (i + 1) < len(lines):
            if not 'iteration' in lines[i + 1]:
                lines[i + 1] = '  ' + lines[i + 1]
                modified = True

        if '\t' in lines[i]:
            lines[i] = lines[i].replace('\t', '  ')
            modified = True

        if 'TabError:' in lines[i]:
            lines[i] = '  ' + lines[i]
            modified = True

        # Remove any special characters
        if '' in lines[i] or '' in lines[i]:
            lines[i] = lines[i].replace('', '  ').replace('', '  ')
            modified = True

        # Ensure a line is indented correctly
        if 'ETA' in lines[i] or '0us/step' in lines[i]:
            lines[i] = ensure_8_spaces(lines[i])
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.writelines(lines)
    return modules

if __name__ == "__main__":
    root_folder = './hard-gists'  # Replace with your folder path
    process_yaml_files(root_folder)


woof = ['os', 'azure-mgmt-azure', 'winreg', 'restful_lib', 'yaml', 'googleapiclient', 'itertools', 'libdnn', 'pyalam', 'npycookiecheat', 'gi', 'pickle', 'xbmc', 'paho', 'mosquitto', 'fontforge', 'create_sentiment_featuresets', 'nfqueue', 'subprocess', 'dateutil', 'hexchat', 'arcpy', '1.4.39', 'plone-standard-library', 'start_1.4.45', 'monkeyrunner', 'ev3dev', 'variety', 'sublimetext', 'sys', 'MicroBit', 'cv2', 'weechat', 'urllib', '1.4.45', 'caffe', 'Cocoa', 'avahi-python', 'microbit', 'cnn', 'gl', 'collections', 'naturaltoken', 'inspect', 'sublime_api', 'openerp', 'python-appindicator', 'pinder', 'tkinter']
