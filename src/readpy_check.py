import os

# Set the root directory you want to search
root_dir = './../hard-gists-readpy'

# Output file where missing paths will be recorded
missing_file_log = 'missing_output.txt'

# Open the log file in write mode
with open(missing_file_log, 'w') as log_file:
    # Loop through each directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check if 'output.txt' exists in the current directory
        if 'output.txt' not in filenames:
            # Write the path of the folder missing 'output.txt' to the log file
            log_file.write(f"{dirpath}\n")

print(f"List of folders missing 'output.txt' has been saved to: {missing_file_log}")
