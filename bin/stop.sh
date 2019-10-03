#!/bin/bash

# Reading addresses and ports from the simplepre config file
SRV_ADDR=$( grep server_addr simplepre/config/config.yml | awk '{print $NF}' )
SRV_ADDR=${SRV_ADDR//\"/}; SRV_ADDR=${SRV_ADDR//\'/}
SRV_PORT=$( grep server_port simplepre/config/config.yml | awk '{print $NF}' )

# Brutefir
pkill -f "simplepre/config/brutefir_config"

# zita receiver
~/simplepre/bin/zita-n2j_mcast.py stop

# Jack connections will be auto vanished

# The Control Server
echo "shutdown" | nc -C $SRV_ADDR $SRV_PORT

