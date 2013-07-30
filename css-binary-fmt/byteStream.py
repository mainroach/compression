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
import struct

#this is a silly little byte stream reader/writer class
#===================================
class ByteStreamWriter(object):
    _array=bytes()
    _endianMode="" #"" = don't care, "<" little endian, ">" big endian
    #http://docs.python.org/3.0/library/struct.html
    def writeString(self,strng,writeLen=True):
        if isinstance(strng, unicode):
            strng = strng.encode("ascii","ignore")
            
        ln = len(strng)
        if(writeLen):
            if ln > 0x80000:
                print "SHIT SHIT SHIT"
            self.writeUShort(ln | 0x8000)
        self._array += struct.pack(str(ln) +"s",bytes(strng))



    def writeByte(self,val):
        self._array += struct.pack(self._endianMode+"b",val)

    def writeUByte(self,val):
        self._array += struct.pack(self._endianMode+"B",val)

    def writeShort(self,val):
        self._array += struct.pack(self._endianMode+"h",val)

    def writeUShort(self,val):
        self._array += struct.pack(self._endianMode+"H",val)

    def writeInt(self,val):
        self._array += struct.pack(self._endianMode+"i",val)
        
    def writeUInt(self,val):
        self._array += struct.pack(self._endianMode+"I",val)

    def writeFloat(self,val):
        self._array += struct.pack(self._endianMode+"f",val)
#===================================
class ByteStreamReader(object):
    _pos =0
    _array=bytes()
    _endianMode="" #"" = don't care, "<" little endian, ">" big endian

    def readByte(self):
        v= struct.unpack_from(self._endianMode+"b",self._array[self._pos])[0]
        self._pos+=1
        return v

    def readUByte(self):
        v= struct.unpack_from(self._endianMode+"B",self._array[self._pos])[0]
        self._pos+=1
        return v

    def readString(self,readLen=0):

        if readLen ==0:
            readLen = self.readUShort()
        v = struct.unpack_from(str(readLen) + "s",self._array[self._pos : self._pos+readLen])[0]
        self._pos+=readLen
        return v

    def readShort(self):
        v = struct.unpack_from(self._endianMode+"h",self._array[self._pos:self._pos+2])[0]
        self._pos+=2
        return v

    def readUShort(self):
        v = struct.unpack_from(self._endianMode+"H",self._array[self._pos:self._pos+2])[0]
        self._pos+=2
        return v

    def readInt(self):
        v = struct.unpack_from(self._endianMode+"i",self._array[self._pos:self._pos+4])[0]
        self._pos+=4
        return v

    def readUInt(self):
        v = struct.unpack_from(self._endianMode+"I",self._array[self._pos:self._pos+4])[0]
        self._pos+=4
        return v

    def readFloat(self):
        v = struct.unpack_from(self._endianMode+"f",self._array[self._pos:self._pos+4])[0]
        self._pos+=4
        return v

    def eos(self):
        return self._pos == len(self._array)