# slim-serv
A barebones lightweight home server setup for direct zigbee and weather-to-eink control.

Zigbee2MQTT runs in docker. A simple Python script that gives full access to set states in Z2M based on its outputs runs in systemctl.


# Pairing Devices
Go to Z2M web UI; `http://<YOUR_RPI_IP>:8080`, and click "Permit Join (All)". Then put the devices in pairing mode, and add and rename them as they pop up. Renaming is crucial. The MQTT Topics will use the friendly name that is chosen.

# Configuring
Lights are configured in `python-controller/lighting.py`


# Setting up

## Python Env
From the `slim-serv/python-controller` directory, run:

### Create a virtual environment named 'venv'
`python3 -m venv venv`

### Activate it
`source venv/bin/activate`

### Install the dependencies
`pip install -r requirements.txt`

## Systemd setup
`sudo nano /etc/systemd/system/slim-serv.service`

Insert the following code
```
[Unit]
Description=SLIM-SERV E-ink and Zigbee Controller
# Wait for Docker (MQTT/Z2M) and the network to be up before starting
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=simple
User=amund
WorkingDirectory=/home/amund/git/slim-serv/python-controller

# Use the Python executable inside your virtual environment
ExecStart=/home/amund/git/slim-serv/python-controller/venv/bin/python main.py

# Bulletproof restarting
Restart=always
RestartSec=10

# Logging: Trash standard output, keep errors in the RAM disk
StandardOutput=null
StandardError=file:/var/log/ramdisk/slim-serv-error.log

[Install]
WantedBy=multi-user.target
```

## Enable and start service

### Reload systemd to recognize the new file
`sudo systemctl daemon-reload`

### Enable it to start automatically on every boot
`sudo systemctl enable slim-serv.service`

### Start the service right now
`sudo systemctl start slim-serv.service`

## Checking status

**Check if it's actively running**

`sudo systemctl status slim-serv.service`

**Read the active error logs**

`cat /var/log/ramdisk/slim-serv-error.log`