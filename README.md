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

Installation

To use this tool, you need to have the following dependencies installed:

    Python 3.x
    sublist3r, subfinder, assetfinder, findomain tools (ensure they are installed and available in your PATH)
