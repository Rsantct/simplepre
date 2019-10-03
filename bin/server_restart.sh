#!/bin/bash

# Reading addresses and ports from the simplepre config file
SRV_ADDR=$( grep server_addr simplepre/config/config.yml | awk '{print $NF}' )
SRV_ADDR=${SRV_ADDR//\"/}; SRV_ADDR=${SRV_ADDR//\'/}
SRV_PORT=$( grep server_port simplepre/config/config.yml | awk '{print $NF}' )

echo "shutdown" | nc -C $SRV_ADDR $SRV_PORT

sleep .25

python3 ~/simplepre/bin/server.py simplecontrol &
