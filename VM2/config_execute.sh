#!/bin/sh

pip install -r ../requirements.txt

sudo cp interfaces /etc/network/interfaces

sudo apt update

sudo apt install ufw

sudo ufw enable

sudo ufw default deny forward

sudo ufw default deny route

sudo ufw allow from any to 192.168.1.254 port 443