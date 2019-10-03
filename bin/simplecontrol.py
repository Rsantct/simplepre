#!/usr/bin/env python3

# This file is part of 'simplepre'

# This module is based on pre.di.c, a preamp and digital crossover
# https://github.com/rripio/pre.di.c
# Copyright (C) 2018 Roberto Ripio
#
# pre.di.c is based on FIRtro https://github.com/AudioHumLab/FIRtro
# Copyright (c) 2006-2011 Roberto Ripio
# Copyright (c) 2011-2016 Alberto Miguélez
# Copyright (c) 2016-2018 Rafael Sánchez
#
# 'simplepre' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'simplepre' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'simplepre'.  If not, see <https://www.gnu.org/licenses/>.

import misc
import socket
import sys
import jack
import math as m
import numpy as np
import yaml
import os

STATE_PATH      = misc.STATE_PATH
EQ_FOLDER       = misc.EQ_FOLDER
CONFIG          = misc.CONFIG

AUDIO_PORTS     = 'brutefir:in.L', 'brutefir:in.R'


## initialize

# EQ curves
try:
    curves = {
        'freq'                : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['frequencies']}"         ),
        'loudness_mag_curves' : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['loudness_mag_curves']}" ),
        'loudness_pha_curves' : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['loudness_pha_curves']}" ),
        'treble_mag'          : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['treble_mag_curves']}"   ),
        'treble_pha'          : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['treble_pha_curves']}"   ),
        'bass_mag'            : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['bass_mag_curves']}"     ),
        'bass_pha'            : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['bass_pha_curves']}"     ),
        'target_mag'          : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['target_mag']}"     ),
        'target_pha'          : np.loadtxt( f"{EQ_FOLDER}/{CONFIG['target_pha']}"     )
        }
except:
    print('Failed to load EQ files')
    sys.exit(-1)


def bf_cli(command):
    """send commands to brutefir"""

    global warnings
    with socket.socket() as s:
        try:
            addr = CONFIG['bf_addr']
            port = CONFIG['bf_port']
            s.connect( (addr, port) )
            command = command + '; quit\n'
            s.send(command.encode())
        except:
            warnings.append (f'Brutefir error at {bf_addr}:{bf_port}')
            
            
def read_full_command(full_command):

    # The full_command sintax:  <command> <arg> add
    # 'add' is given as an option for relative values ordering
    command_is_valid = True
    add = False
    cmd_list = full_command.replace('\r','').replace('\n','').split()
    command = cmd_list[0]
    if cmd_list[1:]:
        arg = cmd_list[1]
        if cmd_list[2:]:
            if cmd_list[2] == 'add':
                add = True
            else:
                command_is_valid = False
    else:
        arg = None

    return command, arg, add, command_is_valid
	

########################################
# Main function for command processing
########################################
def process_commands(  full_command,
                        state = misc.read_yaml(STATE_PATH),
                        curves = curves):
    """ Processes commands for predic control
        Input:  command phrase, state dictionary, curves
        Output: new state dict, warnings
    """

    state_old   = state.copy()
    warnings    = []

    # Processing the full_command, if command is NOT valid, will do nothing.
    command, arg, add, command_is_valid = read_full_command(full_command)
    if not command_is_valid:
        # Do nothing
        warnings.append('Command error')
        return (state, warnings)

    # We need to cal gain because we only manage 'level' inside the state file
    gain        = misc.calc_gain( state['level'] )


    ###########################################################
    # 'change_xxxxx' are the actions to be done as parsed below
    ###########################################################

    def change_mono(mono):
        # this is a pseudo command just for backwards compatibility
        # here we translate mono:on|off to midside:on|off
        
        try:
            tmp = {
                'on':       'mid',
                'off':      'off',
                'toggle':   {'off':'mid', 'side':'off', 'mid':'off'
                             }[ state['midside'] ]
                }[mono]
            return change_midside(tmp, state=state)

        except KeyError:
            warnings.append('Command \'mono ' + arg + '\' is incorrect')
        

    def change_midside(midside, state=state):

        if midside in ['mid', 'side', 'off']:
            state['midside'] = midside
            try:
                if   state['midside']=='mid':
                    bf_cli( 'cfia 0 0 m0.5 ; cfia 0 1 m0.5  ;'
                            'cfia 1 0 m0.5 ; cfia 1 1 m0.5   ')

                elif state['midside']=='side':
                    bf_cli( 'cfia 0 0 m0.5 ; cfia 0 1 m-0.5 ;'
                            'cfia 1 0 m0.5 ; cfia 1 1 m-0.5  ')

                elif state['midside']=='off':
                    bf_cli( 'cfia 0 0 m1   ; cfia 0 1 m0    ;'
                            'cfia 1 0 m0   ; cfia 1 1 m1     ')
            except:
                state['midside'] = state_old['midside']
                warnings.append('Something went wrong when changing '
                                'midside state')
        else:
            state['midside'] = state_old['midside']
            warnings.append('bad midside option: has to be "mid", "side"'
                                ' or "off"')
        return state


    def change_solo(solo, state=state):
        # new function w/o bf_cli, it delegates to change_gain()

        if solo in ['off', 'l', 'r']:
            state['solo'] = solo
            try:
                state = change_gain(gain)
            except:
                state['solo'] = state_old['solo']
                warnings.append('Something went wrong '
                                'when changing solo state')
        else:
            state['solo'] = state_old['solo']
            warnings.append('bad solo option: has to be "l", "r" or "off"')

        return state


    def change_mute(mute, state=state):

        try:
            state['muted'] = {
                'on':       True,
                'off':      False,
                'toggle':   not state['muted']
                }[mute]
        except KeyError:
            state['muted'] = state_old['muted']
            warnings.append('Option ' + arg + ' incorrect')
            return state

        try:
            state = change_gain(gain)
        except:
            state['muted'] = state_old['muted']
            warnings.append('Something went wrong when changing mute state')

        return state


    def change_loudness_track(loudness_track, state=state):

        try:
            state['loudness_track'] = {
                'on':       True,
                'off':      False,
                'toggle':   not state['loudness_track']
                }[loudness_track]
        except KeyError:
            state['loudness_track'] = state_old['loudness_track']
            warnings.append('Option ' + arg + ' incorrect')
            return state
        try:
            state = change_gain(gain)
        except:
            state['loudness_track'] = state_old['loudness_track']
            warnings.append('Something went wrong when changing loudness_track state')
        return state


    def change_loudness_ref(loudness_ref, state=state, add=add):
        try:
            state['loudness_ref'] = (float(loudness_ref)
                                    + state['loudness_ref'] * add)
            state = change_gain(gain)
        except:
            state['loudness_ref'] = state_old['loudness_ref']
            warnings.append('Something went wrong when changing loudness_ref state')
        return state


    def change_treble(treble, state=state, add=add):

        try:
            state['treble'] = (float(treble)
                                    + state['treble'] * add)
            state = change_gain(gain)
        except:
            state['treble'] = state_old['treble']
            warnings.append('Something went wrong when changing treble state')
        return state


    def change_bass(bass, state=state, add=add):

        try:
            state['bass'] = (float(bass)
                                    + state['bass'] * add)
            state = change_gain(gain)
        except:
            state['bass'] = state_old['bass']
            warnings.append('Something went wrong when changing bass state')
        return state


    def change_level(level, state=state, add=add):
        try:
            state['level'] = ( float(level) + state['level'] * add )
            gain = misc.calc_gain( state['level'] )
            state = change_gain(gain)
        except:
            state['level'] = state_old['level']
            warnings.append('Something went wrong when changing %s state'
                                                                % command)
        return state


    def change_gain(gain, state=state):
        """change_gain, aka 'the volume machine' :-)"""

        # gain command send its str argument directly
        gain = float(gain)

        def change_eq():

            eq_str = ''
            l = len(curves['freq'])
            for i in range(l):
                eq_str = eq_str + str(curves['freq'][i]) + '/' + str(eq_mag[i])
                if i != l:
                    eq_str += ', '
            bf_cli('lmc eq "c.eq" mag ' + eq_str)
            eq_str = ''
            for i in range(l):
                eq_str = eq_str + str(curves['freq'][i]) + '/' + str(eq_pha[i])
                if i != l:
                    eq_str += ', '
            bf_cli('lmc eq "c.eq" phase ' + eq_str)


        def change_loudness():

            # Curves available:
            loud_i_min  = 0
            loud_i_max  = curves['loudness_mag_curves'].shape[1] - 1
            # and the flat one:
            loud_i_flat = CONFIG['loudness_index_flat']
            
            if state['loudness_track']:
                loud_i = loud_i_flat - state['level'] - state['loudness_ref']
            else:
                loud_i = loud_i_flat
            
            # clamp index and convert to integer
            loud_i = max( min(loud_i, loud_i_max), loud_i_min )
            loud_i = int(round(loud_i))

            eq_mag = curves['loudness_mag_curves'][:,loud_i]
            eq_pha = curves['loudness_pha_curves'][:,loud_i]
            return eq_mag, eq_pha


        def change_treble():

            treble_i = CONFIG['tone_variation'] - state['treble']
            if treble_i < 0:
                treble_i = 0
            if treble_i > 2 * CONFIG['tone_variation']:
                treble_i = 2 * CONFIG['tone_variation']
            # force integer
            treble_i = int(round(treble_i))
            eq_mag = curves['treble_mag'][:,treble_i]
            eq_pha = curves['treble_pha'][:,treble_i]
            state['treble'] = CONFIG['tone_variation'] - treble_i
            return eq_mag, eq_pha


        def change_bass():

            bass_i = CONFIG['tone_variation'] - state['bass']
            if bass_i < 0:
                bass_i = 0
            if bass_i > 2 * CONFIG['tone_variation']:
                bass_i = 2 * CONFIG['tone_variation']
            # force integer
            bass_i = int(round(bass_i))
            eq_mag = curves['bass_mag'][:,bass_i]
            eq_pha = curves['bass_pha'][:,bass_i]
            state['bass'] = CONFIG['tone_variation'] - bass_i
            return eq_mag, eq_pha


        def commit_gain():
	
            bf_atten_dB_L = gain
            bf_atten_dB_R = gain
            # add balance dB gains
            if abs(state['balance']) > CONFIG['balance_variation']:
                state['balance'] = m.copysign(
                        CONFIG['balance_variation'] ,state['balance'])
            bf_atten_dB_L = bf_atten_dB_L - (state['balance'] / 2)
            bf_atten_dB_R = bf_atten_dB_R + (state['balance'] / 2)

            # From dB to a multiplier to implement easily
            # polarity and mute.
            # Then channel gains are the product of
            # gain, polarity, mute and solo

            m_mute = {True: 0, False: 1}[ state['muted'] ]

            #m_polarity_L = {'+' :  1, '-' : -1,
            #                '+-':  1, '-+': -1 }[ state['polarity'] ]
            #m_polarity_R = {'+' :  1, '-' : -1,
            #                '+-': -1, '-+':  1 }[ state['polarity'] ]
			#
            # 'simplepre' version:
            m_polarity_L = 1
            m_polarity_R = 1

            m_solo_L  = {'off': 1, 'l': 1, 'r': 0}[ state['solo'] ]

            m_solo_R  = {'off': 1, 'l': 0, 'r': 1}[ state['solo'] ]

            m_gain = lambda x: m.pow(10, x/20) * m_mute
            m_gain_L = ( m_gain( bf_atten_dB_L )
                            * m_polarity_L * m_solo_L )
            m_gain_R = ( m_gain( bf_atten_dB_R )
                            * m_polarity_R * m_solo_R )

            # commit final gain change will be applied to the
            # 'from filters' input section on drc filters (cffa)
            bf_cli(      'cffa "f.drc.L" "f.eq.L" m' + str(m_gain_L)
                    + ' ; cffa "f.drc.R" "f.eq.R" m' + str(m_gain_R))


        # backs up actual gain
        gain_old = gain
        # EQ curves: loudness + treble + bass
        l_mag,      l_pha      = change_loudness()
        t_mag,      t_pha      = change_treble()
        b_mag,      b_pha      = change_bass()
        # compose EQ curves with target
        eq_mag = curves['target_mag'] + l_mag + t_mag + b_mag
        eq_pha = curves['target_pha'] + l_pha + t_pha + b_pha
        # calculate headroom
        headroom = misc.calc_headroom(gain, abs(state['balance']/2), eq_mag)
        # if enough headroom commit changes
        if headroom >= 0:
            commit_gain()
            change_eq()
            state['level'] = misc.calc_level(gain)
        # if not enough headroom tries lowering gain
        else:
            change_gain(gain + headroom)
            print('headroom hitted, lowering gain...')
        return state

    ##########################################################
    ## parsing commands and selecting the corresponding action
    ##########################################################
    try:
        state = {
            'solo':             change_solo,
            'mono':             change_mono,
            'midside':          change_midside,
            'mute':             change_mute,
            'loudness_track':   change_loudness_track,
            'loudness_ref':     change_loudness_ref,
            'treble':           change_treble,
            'bass':             change_bass,
            'level':            change_level,
            'gain':             change_gain
            }[command](arg)
            
    except KeyError:
        warnings.append(f"Unknown command '{command}'")
    
    except:
        warnings.append(f"Problems in command '{command}'")

    # return a dictionary of predic state
    return (state, warnings)

##############################################
# Interface function to plug this on server.py
##############################################
def do( cmdline ):
    """ Returns:
        - The state dictionary if cmdline = 'status'
        - 'OK' if the command was succesfully processed.
        - 'ACK' if not.
    """

    result = ''

    # 'status' will read the state file and send it back as an YAML string
    if cmdline.rstrip('\r\n') == 'status':    
        result = yaml.dump( misc.read_yaml(STATE_PATH), default_flow_style=False )

    # Any else cmdline phrase will be processed by the 'proccess_commands()' function,
    # that answers with a state dict, and warnings if any:
    else:
        (state, warnings) = process_commands( cmdline )

        try:
            ############################
            # Here we UPDATE state.yml #
            ############################
            with open( STATE_PATH, 'w' ) as f:
                yaml.dump( state, f, default_flow_style=False )

            # Prints warnings
            if len(warnings) > 0:
                print("Warnings:")
                for w in warnings:
                    print('\t', w)
                result = 'ACK\n'
            else:
                result = 'OK\n'
        except:
            result = 'ACK\n'

    # It is expected to return bytes-like things to the server
    return result.encode()
