# Subdomain Finder Tool

This Python script automates the process of finding subdomains for a given domain. It leverages several tools and services to collect subdomain data and performs deduplication to provide a clean list of unique subdomains.
Features

    Integration with Popular Subdomain Enumeration Tools: Uses sublist3r, subfinder, assetfinder, and findomain to gather subdomains.
    Data Fetching from crt.sh: Retrieves subdomain information from crt.sh for additional coverage.
    Deduplication: Removes duplicate entries to ensure the final list contains only unique subdomains.
    File Management: Handles output file creation, appending results, and error handling.

# Prerequisites

Before running the script, ensure you have the following tools installed:

    sublist3r
    subfinder
    assetfinder
    findomain
    Python 3.x
    requests library (pip install requests)

# Usage

Clone the Repository:

        git clone https://github.com/yourusername/subdomain-finder.git
        cd subdomain-finder

Install Required Python Packages:

        pip install requests

Run the Script:

        python sub.py

When prompted, enter the domain name for which you want to find subdomains.

Example Output

The script generates an output file named all_subdomains.txt that contains a list of unique subdomains found from various tools and services.
Troubleshooting

    Ensure all required tools are installed and accessible from your PATH.
    Verify network connectivity if crt.sh or other online services fail.
    Check tool-specific documentation for additional options or updates.

# Contribution

I am actively looking for improvements to this tool. If you find a more successful tool or have suggestions for enhancements, please let me know! Contributions are welcome—feel free to open an issue or submit a pull request.
