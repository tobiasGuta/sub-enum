# Subdomain Finder Tool

This Python script is a comprehensive tool designed to discover and collect subdomains for a given domain. It integrates multiple subdomain enumeration tools and services to provide a consolidated list of subdomains. The script performs the following tasks:

    Run Subdomain Enumeration Tools:
        Sublist3r: A tool to enumerate subdomains using various search engines.
        Subfinder: A fast subdomain discovery tool.
        Assetfinder: A tool to discover assets and subdomains.
        Findomain: A subdomain enumeration tool that searches for subdomains.

    Fetch Subdomains from crt.sh:
        Uses the crt.sh service to retrieve subdomains listed in SSL certificates for the given domain.

    Combine and Deduplicate Results:
        Aggregates the results from all tools and services.
        Removes duplicate entries to ensure a unique list of subdomains.

# Features

    Artistic ASCII Header: Displays a custom ASCII art header at the start of execution.
    Dynamic File Handling: Manages output files and appends results from various tools.
    Error Handling: Includes robust error handling and reporting for each step of the process.
    User Interaction: Prompts the user to enter the domain for which subdomains need to be discovered.

# Prerequisites

Ensure you have the following tools installed and accessible in your system's PATH:

    sublist3r
    subfinder
    assetfinder
    findomain
    Python 3.x with requests library (install via pip install requests)

# Usage

Clone the repository:

    git clone https://github.com/tobiasGuta/sub-enum.git

Navigate to the directory:

    cd sub-enum

Run the script:

    python sub.py

    Enter the domain when prompted.

Output

    All discovered subdomains will be saved in all_subdomains.txt.
    Intermediate results are saved in separate files: sublist3r_output.txt, subfinder_output.txt, assetfinder_output.txt, findomain_output.txt, and crtsh_output.txt.
    Duplicate entries are removed from the final output file.


Acknowledgements

    Sublist3r
    Subfinder
    Assetfinder
    Findomain
    crt.sh
