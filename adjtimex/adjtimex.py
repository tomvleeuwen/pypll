# -*- coding: utf-8 -*-
#
#  adjtimex.py
#  
#  Copyright (c) 2018 Tom van Leeuwen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# This is a simple wrapper around the C function adjtimex.
# The timex and timeval structs are available as ctypes struct.
# Relevant constants are available as well.
#
# Except for some read-only functionality, the adjtimex function
# requires the CAP_SYS_TIME capability. Since scripts can't have
# capabilities, this script either needs to be run as root, or 
# python needs to have the CAP_SYS_TIME capability globally like this:
#
# chgrp timesetters /usr/bin/python3.6
# setcap 'CAP_SYS_TIME+eip' /usr/bin/python3.6

from __future__ import print_function

import ctypes
import os
import errno

_clib = ctypes.CDLL("libc.so.6", use_errno = True)

ADJ_OFFSET=1
ADJ_FREQUENCY=2
ADJ_MAXERROR=4
ADJ_ESTERROR=8
ADJ_STATUS=16
ADJ_TIMECONST=32
ADJ_SETOFFSET=256
ADJ_MICRO=4096
ADJ_NANO=8192
ADJ_TAI=128
ADJ_TICK=16384
ADJ_OFFSET_SINGLESHOT=32769
ADJ_OFFSET_SS_READ=40961

# Status bits
STA_PLL=1
STA_PPSFREQ=2
STA_PPSTIME=4
STA_FLL=8
STA_INS=16
STA_DEL=32
STA_UNSYNC=64
STA_FREQHOLD=128
STA_PPSSIGNAL=256
STA_PPSJITTER=512
STA_PPSWANDER=1024
STA_PPSERROR=2048
STA_CLOCKERR=4096
STA_NANO=8192
STA_MODE=16384
STA_CLK=32768

# Return values
TIME_OK=0
TIME_INS=1
TIME_DEL=2
TIME_OOP=3
TIME_WAIT=4
TIME_ERROR=5
TIME_BAD=5


class Timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long)]

class Timex(ctypes.Structure):
    _fields_ = [("modes", ctypes.c_int),
                ("offset", ctypes.c_long),
                ("freq", ctypes.c_long),
                ("maxerror", ctypes.c_long),
                ("esterror", ctypes.c_long),
                ("status", ctypes.c_int),
                ("constant", ctypes.c_long),
                ("precision", ctypes.c_long),
                ("tolerance", ctypes.c_long),
                ("time", Timeval),
                ("tick", ctypes.c_long),
                ("ppsfreq", ctypes.c_long),
                ("jitter", ctypes.c_long),
                ("shift", ctypes.c_int),
                ("stabil", ctypes.c_long),
                ("jitcnt", ctypes.c_long),
                ("calcnt", ctypes.c_long),
                ("errcnt", ctypes.c_long),
                ("stbcnt", ctypes.c_long),
                ("tai", ctypes.c_int)]

def adjtimex(timex):
    _clib.adjtimex.argtypes = [ctypes.POINTER(Timex)]
    res = _clib.adjtimex(ctypes.pointer(timex))

    if res == -1:
        errno = ctypes.get_errno()
        raise EnvironmentError(errno, "%d: %s" % (errno, os.strerror(errno)))

    return res
