import struct

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
                print "Data to big to encode this way"
            self.writeUShort(ln)
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

    def writeLong(self,val):
        self._array += struct.pack(self._endianMode+"q",val)
        
    def writeULong(self,val):
        self._array += struct.pack(self._endianMode+"Q",val)

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

    def readLong(self):
        v = struct.unpack_from(self._endianMode+"q",self._array[self._pos:self._pos+8])[0]
        self._pos+=4
        return v

    def readULong(self):
        v = struct.unpack_from(self._endianMode+"Q",self._array[self._pos:self._pos+8])[0]
        self._pos+=4
        return v
    def readFloat(self):
        v = struct.unpack_from(self._endianMode+"f",self._array[self._pos:self._pos+4])[0]
        self._pos+=4
        return v

    def eos(self):
        return self._pos == len(self._array)