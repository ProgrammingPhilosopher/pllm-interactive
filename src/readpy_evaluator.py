import os

# Set the root directory you want to start the search from
root_dir = './../hard-gists-readpy'

# List to store paths of folders missing the 'output.txt' file
missing_output_folders = []

# Loop through each directory and its subdirectories
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Check if 'output.txt' exists in the current directory
    if 'output.txt' not in filenames:
        # Add the current directory to the list if 'output.txt' is missing
        missing_output_folders.append(dirpath)

# Define a file to save the list of missing folders
missing_log_file = 'missing_output_folders.txt'

# Save the missing folder paths to a file for reference
with open(missing_log_file, 'w') as log_file:
    for folder in missing_output_folders:
        log_file.write(f"{folder}\n")

print(f"Folders missing 'output.txt' have been saved to: {missing_log_file}")




