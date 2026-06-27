#!/bin/bash
# Run on AWS EC2 (t2.micro) after SSH login to add 2GB swap for Ollama.
# Usage: bash deploy/setup-ec2-swap.sh

set -e

if [ -f /swapfile ]; then
  echo "Swap file already exists."
  swapon --show
  free -h
  exit 0
fi

echo "Creating 2GB swap file..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

if ! grep -q '/swapfile' /etc/fstab; then
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "Swap enabled:"
free -h
