# Subdomain Finder Tool


This Python script is a comprehensive tool designed to discover and collect subdomains for a given domain. It integrates multiple subdomain enumeration tools and services to provide a consolidated list of subdomains. The script performs the following tasks:

https://github.com/user-attachments/assets/d5ab6a9e-ed16-4d2e-96d1-be302520f791

### Improvements

- **Domain Filtering**  
  Added filtering to ensure that only subdomains of the specified target domain are saved in `all_subdomains.txt`.

- **Deduplication**  
  Deduplication is explicitly enforced using a set, both when filtering initial subdomains and when saving results after `dnsx` and `httpx`, ensuring only unique entries.

- **Live Subdomain Validation**  
  Integrated `dnsx` to resolve DNS for each subdomain and `httpx` to check for live HTTP services. Only live, reachable subdomains are saved to the output, improving data relevance.

- **Output Display Control**  
  Added a prompt at the end asking the user if they’d like to view the contents of `all_subdomains.txt`, allowing for optional result display.

- **Code Structure & Modularity**  
  Refactored code into distinct functions, with clear function names and comments. Each major step (e.g., filtering, deduplication, saving) is broken down for easier readability and maintenance.

- **Enhanced Error Handling**  
  Structured error handling provides specific error messages if a command fails or if a tool is missing, utilizing `subprocess` exceptions and checks for tool availability before execution.

- **Dynamic Loading Indicators**  
  Implemented a loading circle to show that a tool is running, followed by a `✅` or `❌` mark at the end to indicate success or failure.

- **Progress Simulation**  
  Realistic progress is simulated using a rotating spinner (`|`, `/`, `-`, `\`) that updates continuously until each command completes.



    Run Subdomain Enumeration Tools:
        Sublist3r
        Subfinder
        Assetfinder
        Findomain

    Fetch Subdomains from crt.sh:
        Uses the crt.sh service to retrieve subdomains listed in SSL certificates for the given domain.

    Combine and Deduplicate Results:
        Removes duplicate entries to ensure a unique list of subdomains.

# Features

        Artistic ASCII Header: Displays a custom ASCII art header at the start of execution.
        Error Handling: Includes robust error handling and reporting for each step of the process.
        User Interaction: Prompts the user to enter the domain for which subdomains need to be discovered.

# Prerequisites

Ensure you have the following tools installed and accessible in your system's PATH:

    sublist3r
    subfinder
    assetfinder
    findomain
    dnsx
    httpx
    Python 3.x with requests library (install via pip install requests)

# Usage

Clone the repository:

    git clone https://github.com/tobiasGuta/sub-enum.git

Navigate to the directory:

    cd sub-enum

Run the script:

    python3 sub.py

    Enter the domain when prompted.

# Output

    All discovered subdomains will be saved in all_subdomains.txt.
    Duplicate entries are removed from the final output file.


# Acknowledgements

    Sublist3r
    Subfinder
    Assetfinder
    Findomain
    crt.sh
    dnsx
    httpx

# Future Updates

    I am committed to continually improving this tool. Future updates will include integrations with additional subdomain discovery tools and services. Stay tuned for enhancements that will further expand        its capabilities and provide even more comprehensive results for subdomain enumeration.
    Feel free to open issues or submit pull requests if you have suggestions for additional tools or features to include.
