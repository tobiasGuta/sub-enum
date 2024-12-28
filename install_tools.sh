#!/bin/bash

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
sudo apt install -y subfinder

echo "Installing Assetfinder..."
sudo apt install -y assetfinder

echo "Installing Findomain..."
sudo apt install -y findomain

echo "Installing DNSX..."
sudo apt install -y dnsx

# Install HTTPX using Go
echo "Installing HTTPX..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Verify installations
echo "Verifying installations..."
sublist3r --help && subfinder --help && assetfinder --help && findomain --help && dnsx --help && httpx --help

echo "Installation complete!"
