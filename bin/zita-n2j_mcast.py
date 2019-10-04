#!/usr/bin/env python3

"""
    LAN multicast audio receiver based on zita-n2j from Fons Adriaensen.

    See man zita-njbridge:
    ... similar  to  having analog audio connections between the
    sound cards of the systems using it

    usage:    zita-n2j_mcast   start | stop
"""
###############################
JACKNAME = 'zita-n2j_spre'
###############################

import sys
import subprocess as sp
import os

HOME     = os.path.expanduser("~")

def get_interface_name():
    # Getting the machine's used interface name
    interface = ''
    tmp = sp.check_output('ip route'.split()).decode()
    # Example $ ip route
    # default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.36 metric 202
    for line in tmp.split('\n'):
        if 'default' in line:
            interface = line.split()[4]
    if not interface:
        print( 'init/zita-n2j_mcast: cannot get your network interface name :-/' )
        return False
    return interface

def start():
    interface = get_interface_name()
    # Using a no reserved multicast address 224.0.0.151 and port 65151
    # https://www.iana.org/assignments/multicast-addresses/multicast-addresses.xhtml#multicast-addresses-1
    p = sp.Popen( f'zita-n2j --jname {JACKNAME} --buff 50 224.0.0.151 65151 {interface}'.split() )
    print ('zita process:', p.pid)
    with open(f'{HOME}/simplepre/.zita.pid', 'w') as f:
        f.write( str(p.pid) )

def stop():
    print( f'killing zita-n2j_spre' )
    sp.Popen( f'pkill -KILL -f {JACKNAME}'.split() )

if __name__ == '__main__':

    if sys.argv[1:]:
        option = sys.argv[1]
        if option == 'start':
            start()
        elif option == 'stop':
            stop()
        else:
            print(__doc__)
    else:
        print(__doc__)
