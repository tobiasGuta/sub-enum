# Subdomain Discovery Tool
Overview

This tool is designed to automate the discovery of subdomains for a given domain. It leverages multiple popular tools and techniques to gather subdomain information and compiles the results into a single output file. The tool includes functionalities for running external subdomain enumeration tools, appending their results, and performing Google dorking to uncover additional subdomains.
Features

    Subdomain Enumeration: Runs several subdomain enumeration tools:
        Sublist3r
        Subfinder
        Assetfinder
        Findomain
    Google Dorking: Searches Google for subdomains using a query to enhance discovery.
    Result Aggregation: Collects and aggregates results from different tools into a single output file.

# Installation

To use this tool, you need to have the following dependencies installed:

    Python 3.x
    sublist3r, subfinder, assetfinder, findomain tools (ensure they are installed and available in your PATH)


# Usage

Prepare your environment: Make sure the required external tools are installed and accessible.

Run the tool: Execute the script and provide a domain when prompted.
    
    python your_script_name.py
    
Input the domain: When prompted, enter the domain you wish to enumerate.

Review the results: The results will be saved in a file named all_subdomains.txt. This file will contain subdomains gathered from various tools and Google dorking.

# Notes

    Ensure you have the necessary permissions to run these tools and access their outputs.
    This script assumes that the tools are installed and available in the system’s PATH.

# Contributing

Feel free to fork this repository and submit pull requests. If you encounter issues or have feature requests, please open an issue on GitHub.
