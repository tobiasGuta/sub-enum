import os

# List of files to delete
files_to_delete = [
    'all_subdomains.txt',
    'assetfinder_output.txt',
    'crtsh_output.txt',
    'findomain_output.txt',
    'subfinder_output.txt',
    'sublist3r_output.txt',
    'updomains.txt'
]

# Loop through the list and delete each file
for file in files_to_delete:
    try:
        os.remove(file)
        print(f'Successfully deleted: {file}')
    except FileNotFoundError:
        print(f'File not found: {file}')
    except Exception as e:
        print(f'Error deleting {file}: {e}')
