#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pypll.py
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
# The PyPLL class can be used to keep the time in sync with an external 
# time source. All you need to do to keep the system time in sync
# is pass the offset of the real time vs the local time (see main() below)
#

import time
import logging

import adjtimex

# freq is ppm (parts per million) with a 16-bit fractional part (2^-16  ppm)
SEC_TO_FREQ = 65536000000

# Max offset in seconds before making a step.
MAX_OFFSET = 0.5
# Maximum offset to enter sync state
SYNC_OFFSET = 0.005

class PyPLL(object):
    """ PyPLL
    
        This is a wrapper around the adjtimex module that just accepts 
        an offset and keeps the system clock in sync.
        
        @param max_offset:  Make a timestep if the offset is larger than this value
        @param sync_offset: Enter tracking if offset is smaller than this value.
    """
    FREE_RUNNING=0
    LOCKED=1
    
    def __init__(self, max_offset=MAX_OFFSET, sync_offset=SYNC_OFFSET):
        assert max_offset >= sync_offset
        self.state = self.FREE_RUNNING
        self.max_offset = max_offset
    
    def process_offset(self, offset):
        """ process_offset
        
            Wrapper function to help set up the system clock from a known time offset.
            The first time this function is called, a step is made.
            When offset is too large, a step is made again.
            
            This function is basically all you need to keep the time in sync.
            
            @param offset:  Time offset in (actual_time - system_time)
            
            return None
        """
        # Unlock if the offset becomes too big. Something probably changed.
        # And skip init if offset is low enough.
        if abs(offset) > self.max_offset:
            self.state = self.FREE_RUNNING
        elif abs(offset) < SYNC_OFFSET:
            self.state = self.LOCKED
        
        if self.state == self.FREE_RUNNING:
            logging.info("Making timestep of %e s", offset)
            self.clear_time_state()
            self.timestep(offset)
        else:
            logging.debug("Offset: %e", offset)
            self.set_offset(offset)
        
    def clear_time_state(self):
        """ clear_time_state
        
            Clears the time state so that the clock can be adjusted manually again. 
            
            return: None
        """
        adjtimex.adjtimex(adjtimex.Timex(modes=adjtimex.ADJ_STATUS, status=adjtimex.STA_PLL))
        adjtimex.adjtimex(adjtimex.Timex(modes=adjtimex.ADJ_STATUS))

    def timestep(self, seconds = 0.0):
        """ timestep
        
            Makes a timestep using the provided seconds. Time will be added
            to the system time so a positive value will make the clock go forward.
            
            @param seconds: Number of seconds to adjust the system clock
            
            return: None
        """
        microseconds = int(round(seconds * 1000000))
        seconds_int = int(microseconds // 1000000)
        usec = int(microseconds - (seconds_int * 1000000))
        timeval = adjtimex.Timeval(seconds_int, usec)
        
        timeadj = adjtimex.Timex(modes=adjtimex.ADJ_SETOFFSET | adjtimex.ADJ_MICRO,
                                 time=timeval)
        
        adjtimex.adjtimex(timeadj)
        
    def set_speed(self, factor=1.0):
        """ set_speed 
            
            Sets the system frequency, obtained using get_speed.
            
            @param factor    : Speed of system clock, should be close to 1.0
            
            return: None
        """
        # Tick is always positive, we can round by adding 0.5
        tick = int(factor * 10000 + 0.5)
        remainder = factor - (tick / 10000.0)
        freq = int(round(remainder * SEC_TO_FREQ))
        
        timeadj = adjtimex.Timex(modes=adjtimex.ADJ_FREQUENCY | adjtimex.ADJ_TICK |
                                 adjtimex.ADJ_STATUS,
                                 freq = freq,
                                 tick = tick,
                                 status = adjtimex.STA_PLL)
        adjtimex.adjtimex(timeadj)

    def get_speed(self):
        """ get_speed
        
            Gets the current system clock speed. Can be used to provide to set_speed after a reboot.
            
            return: Speed of system clock, close to 1.0.
        """
        timeadj = adjtimex.Timex(modes=0)
        adjtimex.adjtimex(timeadj)
        
        speed = float(timeadj.tick) / 10000 + float(timeadj.freq) / SEC_TO_FREQ
        
        return speed
    
    def set_offset(self, offset=0.0):
        """ set_offset
        
            Passes the offset to the kernel, making the actual time PLL work.
            
            @param offset:  Time offset in (actual_time - system_time), as passed to the kernel
            
            return: None
        """
            
        offset_us = int(offset * 1000000)
        
        timeadj = adjtimex.Timex(modes=adjtimex.ADJ_OFFSET | adjtimex.ADJ_STATUS | 
                                adjtimex.ADJ_MICRO | adjtimex.ADJ_MAXERROR,
                                offset = offset_us,
                                maxerror = abs(offset_us),
                                status = adjtimex.STA_PLL)
        adjtimex.adjtimex(timeadj)
    
    
def main():
    # Test: Stay in lock with pool.ntp.org.
    logging.basicConfig(level=logging.DEBUG)
    
    import sys
    import ntplib
    
    pll=PyPLL()
    ntp_client = ntplib.NTPClient()
    
    # Tests get_speed and set_speed
    speed = pll.get_speed()
    print("Current frequency: %e" % speed)
    pll.set_speed(speed)
    
    # Basic usage: 
    # 1) Get offset (in this example using NTP),
    # 2) Apply offset.
    while True:
        response = ntp_client.request('pool.ntp.org', version=3)
        pll.process_offset(response.offset)
        time.sleep(16)
    
if __name__ == "__main__":
    main()
