#!/bin/bash

#############################################################################
# IMPORTANT: We assume that your session has a JACK server already running.
#            if not, launch here ;-)
#############################################################################

# The jack ports where your loudspeaker is plugged:
LSPK_L_PORT="system:playback_1"
LSPK_R_PORT="system:playback_2"


# Reading addresses and ports from the simplepre config file
SRV_ADDR=$( grep server_addr simplepre/config/config.yml | awk '{print $NF}' )
SRV_ADDR=${SRV_ADDR//\"/}; SRV_ADDR=${SRV_ADDR//\'/}
SRV_PORT=$( grep server_port simplepre/config/config.yml | awk '{print $NF}' )

### STOPPING STUFF ###

~/simplepre/bin/stop.sh


### STARTING STUFF ###

# The zita receiver
~/simplepre/bin/zita-n2j_mcast.py start >/dev/null 2>&1 &

# Brutefir
/usr/local/bin/brutefir ~/simplepre/config/brutefir_config &

# Connecting things on Jack

# We need to wait for brutefir ports to be active under Jack
cmd="jack_connect  zita-n2j_spre:out_1 brutefir_spre:in.L"
c=0
while (( c<30 )); do
    if $($cmd >/dev/null 2>&1); then
        # remaining connections
        jack_connect  zita-n2j_spre:out_2   brutefir_spre:in.R
        jack_connect  brutefir_spre:fr.L    "$LSPK_L_PORT"
        jack_connect  brutefir_spre:fr.R    "$LSPK_R_PORT"
        break
    else
        echo -n "."
    fi
    sleep 1
    (( c++ ))
done

# The Control Server
python3 ~/simplepre/bin/server.py simplecontrol &
