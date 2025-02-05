#!/bin/bash

# Add Go binaries to the PATH in ~/.zshrc
echo 'export PATH=$PATH:~/go/bin' >> ~/.zshrc

# Update and upgrade the system
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Go (Golang)
echo "Installing Go (Golang)..."
sudo apt install -y golang-go

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
