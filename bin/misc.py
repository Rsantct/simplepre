#!/usr/bin/env python3

# This file is part of 'simplepre'
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

import os
import numpy as np
import yaml

def read_yaml(filepath):
    """ returns dictionary from yaml file"""
    with open(filepath) as f:
        d = yaml.load(f)
    return d

def calc_gain(level):
    gain = (level + LOUDSPEAKER['ref_level_gain'] )
    return gain


def calc_level(gain):
    level = (gain - LOUDSPEAKER['ref_level_gain'] )
    return level


def calc_headroom(gain, balance, eq_mag):
    """ calculate headroom from gain and equalizer """

    headroom = ( CONFIG['gain_max'] - gain - np.max(eq_mag)
                    - abs(balance/2))
    return headroom


def read_target():
    target_mag = np.loadtxt( EQ_FOLDER + '/' + CONFIG['target_mag'] )
    target_pha = np.loadtxt( EQ_FOLDER + '/' + CONFIG['target_pha'] )    
    return target_mag, target_pha


HOME            = os.path.expanduser("~")
STATE_PATH      = f'{HOME}/simplepre/.state.yml'
EQ_FOLDER       = f'{HOME}/simplepre/eq'
CONFIGFOLDER    = f'{HOME}/simplepre/config'
CONFIGFILE      = f'{CONFIGFOLDER}/config.yml'
CONFIG          = read_yaml(CONFIGFILE)
LOUDSPEAKER     = CONFIG['loudspeaker']
