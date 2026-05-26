#!/bin/bash
set -e

echo "Setting up RAM disk for logs..."
sudo mkdir -p /var/log/ramdisk
sudo chown 1000:1000 /var/log/ramdisk

# Add tmpfs to fstab if it doesn't exist
if ! grep -q "/var/log/ramdisk" /etc/fstab; then
    echo "tmpfs /var/log/ramdisk tmpfs nodev,nosuid,noatime,size=50M 0 0" | sudo tee -a /etc/fstab
    sudo mount -a
fi

echo "Creating config directories..."
mkdir -p ./mosquitto ./zigbee2mqtt

echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

echo "Host setup complete! Please log out and back in, then run: docker compose up -d"