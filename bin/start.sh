#!/bin/bash

#############################################################################
# IMPORTANT: We assume that your session has a JACK server already running.
#            if not, launch here ;-)
#############################################################################

LSPK_L_PORT="system:playback_1"
LSPK_R_PORT="system:playback_2"


# Reading addresses and ports from the simplepre config file
SRV_ADDR=$( grep server_addr ~/simplepre/config/config.yml | awk '{print $NF}' )
SRV_ADDR=${SRV_ADDR//\"/}; SRV_ADDR=${SRV_ADDR//\'/}
SRV_PORT=$( grep server_port ~/simplepre/config/config.yml | awk '{print $NF}' )

##################
# STOPPING STUFF
##################

~/simplepre/bin/stop.sh


##################
# STARTING STUFF
##################

# The zita receiver
~/simplepre/bin/zita-n2j_mcast.py start >/dev/null 2>&1 &

# Brutefir
/usr/local/bin/brutefir ~/simplepre/config/brutefir_config &
c=0
echo waiting for Brutefir ports under Jack ...
while true; do
    echo -n '.'
    tmp=$(jack_lsp brutefir_spre)
    if [ ! -z "$tmp" ]; then
        break
    fi
    sleep .5
    (( c ++ ))
    if [ "$c" -ge 120 ]; then
        exit -1
    fi
done

# Connecting things on Jack
jack_connect    brutefir_spre:in.L     zita-n2j_spre:out_1
jack_connect    brutefir_spre:in.R     zita-n2j_spre:out_2
jack_connect    brutefir_spre:fr.L     "$LSPK_L_PORT"
jack_connect    brutefir_spre:fr.R     "$LSPK_R_PORT"


# The Control Server
python3 ~/simplepre/bin/server.py simplecontrol &
