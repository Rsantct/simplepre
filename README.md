# simplepre

A simple PC based preamplifier

Just another preamplifier based on Jack and Brutefir

This is a simplified version of FIRtro / pre.di.c

Here we do not manage:

    - inputs
    - drc filter sets
    - xover filter sets
    - loudspeakers sets
    
Here we do manage:

    - Volume control with Loudness compensation.
    - Mono/Stereo control
    - Tone control

This can work alongside a full pre.di.c or FIRtro system, 
for instance, you can use some unused sound card channel
under a running Jack system.

A multicast LAN to Jack is provided.

