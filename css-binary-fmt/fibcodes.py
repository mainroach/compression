'''Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
#limitations under the License.'''

import sys
import os
import math
import byteStream
import bitStream
import re


def F3(n):
    if n <= 0: return 0
    elif n == 1: return 1
    else: return F3(n-1)+F3(n-2)+F3(n-3)

def genFib3Codes(numCodes):
    '''
    Generate FIB3 codes based on http://comjnl.oxfordjournals.org/content/53/6/701.short
    '''
    
    codes=[]
    codes.append([0x07,3]) #stack the first one
    
    symbolCount =1

    # A fib M code consists of a prefix, and suffix
    # The suffix is full of '1's, length equal to M, where M is 2, 3, 4 
    # The prefix is 'groupIndex' bits long, where groupIndex increases from 1,X
    # The prefix data is composed of [0,Q], where Q = Fib3(groupIndex) (if M == 3)
    #   and then those bits are reversed
    groupIdx = 0
    while symbolCount < numCodes:

        groupCt = F3(groupIdx) #figure out how many numbers are in this fib group

        bitSize= groupIdx #bit size is always equal to whatever our fib index is
        for n in range(groupCt):
            #http://stackoverflow.com/questions/12681945/reversing-bits-of-python-integer
            b = '{:0{width}b}'.format(n, width=bitSize)
            code =  (int(b[::-1], 2)<<3) | 0x07 # note, for these fib codes we shift 3 bits into the lower position
            #print bin(code)

            codes.append([code,bitSize+3])

            symbolCount +=1
            if symbolCount >= numCodes: break
      
        if symbolCount >= numCodes: break
        groupIdx +=1

    return codes



    