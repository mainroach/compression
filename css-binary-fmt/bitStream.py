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

#this is a sille little bit-straem reader/writer class. 
import sys
import math
#=========================================
class BitStream(object):
    mArray=[0]
    mBucketIdx=0
    mBitIdx=0
    mBitCount=0

    def __init__(self):
        self.mArray=[0]
        self.mBucketIdx = 0
        self.mBitIdx=0
        self.mBitCount=0

    def setArray(self,arr):
        self.mArray = arr
        self.mBitCount = len(arr)*8

    def add(self,v):
        bitMask = 0x80 >> self.mBitIdx
        if(v):
            self.mArray[self.mBucketIdx] |= bitMask;
        

        if(self.mBitIdx + 1 >= 8):
            self.mArray.append(0)
            self.mBucketIdx+=1
            self.mBitIdx = 0
        else:
            self.mBitIdx += 1

        self.mBitCount+=1

    def addSubInt32(self,v,numLowBits):
        #numLowBits represents the lowest X bits to keep
        tk = v
        for i in range(numLowBits):
            shiftIdx = (numLowBits-1-i)
            #print shiftIdx
            msk = 0x01 << shiftIdx
            self.add(tk & msk)
        

    def getValue(self,bitIdx):
        charIdx = int(bitIdx / 8)
        subIdx = int(bitIdx % 8)
        msk = 0x80 >> subIdx
        if(charIdx >= len(self.mArray)):
            print "error, exceeded bit count"
            return 0
        return self.mArray[charIdx] & msk > 0

    def setValue(self,bitIdx,value):
        charIdx = int(bitIdx / 8)
       
        if(charIdx >= len(self.mArray)):
            print "error, exceeded bit count"

        subIdx = int(bitIdx % 8)
        msk = 0x80 >> subIdx
        if value:
            self.mArray[charIdx] |= msk
        else:
            self.mArray[charIdx] &= ~msk

    

    def readBits(self,start,length,tempHolder):

        bini = (start / 8) | 0 #what array index are we
        idx = start % 8    #what start bit in the array
        
        numBitsHere = min(8-idx,length) #figure the number of bits we need for this element
        msk = (0xFF&(0xFF << (8-numBitsHere)))>> idx #create a bit mask and shift it to the target loaction    
        #grab the bits from this byte, and then shift them towards LSB
        targetBits = (self.mArray[bini] & msk) >> (8-numBitsHere-idx)
    
        lenLeft = min(8,length-numBitsHere)
        tempHolder = tempHolder<< lenLeft
        tempHolder |= targetBits<< lenLeft
        
        start+=numBitsHere;
        if lenLeft==0 or start+ lenLeft>= self.mBitCount:
            return tempHolder
        
        return self.readBits(start,length-numBitsHere,tempHolder)

    def printBlock(self, v):
        msk = 0x80;
        for q in range(8):
            msk = 1;
            msk = msk << (7- q);

            vv = v & msk;
            if(vv):
                sys.stdout.write("1");
            else:
                sys.stdout.write("0");
    
    def printToConsole(self):
        ct = 0

        for i in range((self.mBitCount)):
            vv = self.getValue(i);
            if(vv):
                sys.stdout.write("1");
            else:
                sys.stdout.write("0");
            
        
        sys.stdout.write("\n")

    def toByteArray(self):

        outStream = bytearray()
        for i in range(len(self.mArray)):

            if i * 8 >= self.mBitCount:break
            outStream.append(self.mArray[i])
        return outStream


#=========================================
#=========================================
if __name__ == '__main__':
    bs = BitStream()
    '''
    bs.addSubInt32(0x04,4)
    bs.addSubInt32(0x00BE2D48,32)
    
    print bin(bs.readBits(7,10,0))
    bs.add(True);
    bs.add(True);
    bs.add(True);
    bs.add(False);
    bs.add(False);
    bs.add(False);
    bs.add(True);
    bs.add(False);
    bs.add(False);
    bs.add(False);
    bs.add(True);
    bs.add(False);
    bs.add(False);
    bs.add(False);
    bs.add(True);
    bs.add(True);
    print bs.getValue(2)

    bs.printToConsole();'''

    print v
