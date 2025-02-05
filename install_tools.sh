#!/bin/bash

# Add Go binaries to the PATH in ~/.zshrc
echo 'export PATH=$PATH:~/go/bin' >> ~/.zshrc

# Update and upgrade the system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Go (Golang)
echo "Installing Go (Golang)..."

# Remove any previous Go installation (if it exists)
echo "Removing previous Go installation..."
sudo rm -rf /usr/local/go

# Download the latest Go tarball (replace the version if needed)
echo "Downloading Go..."
wget https://go.dev/dl/go1.23.6.linux-amd64.tar.gz

# Extract the tarball to /usr/local
echo "Extracting Go..."
sudo tar -C /usr/local -xzf go1.23.6.linux-amd64.tar.gz

# Add Go to the PATH environment variable
echo "Adding Go to PATH..."
echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.profile
source ~/.profile

# Verify the Go installation
echo "Verifying Go installation..."
go version

# Install common dependencies
echo "Installing common dependencies..."
sudo apt install -y curl wget unzip python3-pip

# Install required tools using apt
echo "Installing Sublist3r..."
sudo apt install -y sublist3r

echo "Installing Subfinder..."
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

echo "Installing Assetfinder..."
sudo apt install -y assetfinder

echo "Installing Findomain..."
sudo apt install -y findomain

echo "Installing DNSX..."
sudo apt install -y dnsx

# Remove HTTPX if it exists
echo "Removing existing HTTPX binary if present..."
sudo rm -rf /usr/bin/httpx

# Install HTTPX using Go
echo "Installing HTTPX..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Verify installations
echo "Verifying installations..."
sublist3r --help && subfinder --help && assetfinder --help && findomain --help && dnsx --help && httpx --help

# Remove unnecessary packages
echo "Removing unnecessary packages..."
sudo apt autoremove -y

#Complete!
echo "Installation complete!"

# Apply changes to ~/.zshrc
echo "please type: source ~/.zshrc"
