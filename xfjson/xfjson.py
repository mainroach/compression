# This Python file uses the following encoding: utf-8
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

import json
import struct
import sys
import math
import shutil, errno
import operator


'''
We transpose a JSON format from ‘array of structs’ to ‘struct of arrays’ and yield benefits 
by the removal of excessive key-labels, yielding 5%-12% size improvements

How it works:
The “key” portion of KV-pairs for most json structures is repeated for each instance of the structure in the file, 
adding bloat to the file. By moving to a SoA form, we reduce this data element, and easily reduce size of the file.
This type of form is quite common, for example, receiving a block of Twitter Data.

There are many edge cases in which post XFJSON content, when GZipp'd results in a larger file than the GZip'd source file alone. Typically this is the case for smaller .css files < 8k in size


Using this module:

COMPRESSION
    -t - Do Transpose (execute the SoA to AoS form)
    -tr - Do Reversible Transpose - Do the same transpose, but mark the data so that you can reverse it back on the client. (useful if you don't want to change your client code)
    -b - Spit out a binary version of the file. Useful to shave another few % off the file itself, which may allow it to decompress ByteStreamWriter

DECOMPRESSION
    -d - Do decompression. Note, all the information needed to decompress the variants of the file are included in the file. You simply need to call 'decompress'
'''



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

class TransposeJSON(object):
    _tranposeMode = 0
    #=========================================
    #we will only pack a list of dictionary objects that do not have child lists, of dictionaries in them...
    def encode(self,jsonObj,transposeMode):
        self._tranposeMode = transposeMode
        #add a flag for the decoder to know we're transposed.
        jsonObj["^"]="1"
        self._encodeContainer(jsonObj)
        #print jsonObj
       
    #=========================================
    def _encodeAoStoSoA(self, jsonObj):
        if len(jsonObj)<=1:return None
        if not isinstance(jsonObj[0], dict): return None

        keys = jsonObj[0].keys()

        #quick scan to see if we can encode this list.
        for q in range(len(jsonObj)):
            tKeys = jsonObj[q].keys()
            if sorted(keys) != sorted(tKeys):
                print "Warning, found an array who's structures keys are not homogeneous for all elements. Skpping it"
                return None

        #g2g, encode the thing.
        #print keys
        struct={}
        for k in keys:
            struct[k]=[]

            for q in range(len(jsonObj)):
                struct[k].append(jsonObj[q][k])
        
        if self._tranposeMode == 2:
            #add a flag for the decoder to know we're transposed.
            struct["^"]="1"

        #print struct
        return struct


    #=========================================
    def _encodeContainer(self,jsonObj):
        
        #dictionaries will contain objects, walk them
        if isinstance(jsonObj, dict):
            
            doReshuffle = False
            for k in jsonObj:
                value = jsonObj[k]
                #try to do a look ahead, if this member is a list, see if we can recode it
                if isinstance(value, list):
                    
                    didShuffle = self._encodeAoStoSoA(value)

                    if didShuffle != None:
                        #A recode occured, re-assign the KVPair to point to the new struct object
                        jsonObj[k] = didShuffle
                        
                        #we issue a re-shuffle on this parent object, to handle multiple nesting layers
                        doReshuffle = True
                        break
                    else:
                        #we're not a re-orderable array, so try to dig deeper
                        self._encodeContainer(value)
                else:
                    #we might have a dictionary, of dictionaries, of lists.
                    self._encodeContainer(value)

            if doReshuffle:
                self._encodeContainer(jsonObj)#trigger a recode since we've changed

            #just walk a raw list forward
        elif isinstance(jsonObj, list):
            for i in range(len(jsonObj)):
                 self._encodeContainer(jsonObj[i])

    #=========================================
    def decode(self,jsonObj):
        
        #if this data isn't transposed, bail.
        if not "^" in jsonObj.keys():
            return 
        jsonObj.pop("^", None) #remove the flag

        self._decodeContainer(jsonObj)
    #=========================================
    def _decodeSoAtoAoS(self, jsonObj):
        jsonObj.pop("^", None) #remove the flag
        keys = jsonObj.keys()
        numItems = len(jsonObj[keys[0]])
        newArr = []

        #
        for q in range(numItems):
            s={}
            for k in keys:
                s[k] = jsonObj[k][q]
            newArr.append(s)

        return newArr
    #=========================================
    def _decodeContainer(self,jsonObj):
        #dictionaries will contain objects, walk them
        if isinstance(jsonObj, dict):
            

            doReshuffle = False
            for k in jsonObj:
                value = jsonObj[k]
                #try to do a look ahead, if this member is a dict, see if we can recode it
                if isinstance(value, dict):
                    
                    if "^" in value:

                        
                    
                        didShuffle = self._decodeSoAtoAoS(value)

                        if didShuffle != None:
                            #A recode occured, re-assign the KVPair to point to the new struct object
                            jsonObj[k] = didShuffle
                            
                            #we issue a re-shuffle on this parent object, to handle multiple nesting layers
                            doReshuffle = True
                            break
                    else:
                        #we're not a re-orderable array, so try to dig deeper
                        self._decodeContainer(value)
                else:
                    #we might have a dictionary, of dictionaries, of lists.
                    self._decodeContainer(value)

            if doReshuffle:
                self._decodeContainer(jsonObj)#trigger a recode since we've changed

            #just walk a raw list forward
        elif isinstance(jsonObj, list):
            for i in range(len(jsonObj)):
                 self._decodeContainer(jsonObj[i])

           
#=========================================
class BinaryJSON(object):
    _binaryStream=None
    _itemToken=0x1A

    _dictStart=0xF0
    _arrayStart=0xC0

    _longStart=0x80
    _floatStart=0x90
    _intStart=0xA0
    _stringStart=0xB0

    #=========================================
    def _numBytesForLen(self, length):
        if length <= 0xFF:
            return 1
        if length <= 0xFFFF:
            return 2

        return 4
    #=========================================
    #we will only pack a list of dictionary objects that do not have child lists, of dictionaries in them...
    def encode(self,jsonObj):
        self._binaryStream = ByteStreamWriter()                    
        self._binaryStream.writeUByte(self._itemToken)
        self._binaryStream.writeUByte(0x00)#flags bit, we'll set this later


        self._encodeContainer(jsonObj)
        return self._binaryStream._array

    #=========================================
    def _encodeContainer(self,jsonObj):
        #print jsonObj.__class__.__name__
        #print jsonObj
        if isinstance(jsonObj, dict):
            #write the 'start dictionary' delemeter
            numItems = len(jsonObj)
            numItemBytes= self._numBytesForLen(numItems)
            combinedTag = self._dictStart | (0x0F & numItemBytes)
            self._binaryStream.writeUByte(combinedTag)

            #now write the number of objects
            self._binaryStream.writeUShort(numItems)
            
            #allow each object to write itself
            for k in jsonObj:
                #print "key " + k
                self._binaryStream.writeString(k)
                self._encodeContainer(jsonObj[k])

        elif isinstance(jsonObj, list):
            #write the 'start dictionary' delemeter
            numItems = len(jsonObj)
            numItemBytes= self._numBytesForLen(numItems)
            combinedTag = self._arrayStart | (0x0F & numItemBytes)
            self._binaryStream.writeUByte(combinedTag)

            #now write the number of objects
            self._binaryStream.writeUByte(numItems)

            #allow each object to write itself
            for k in range(0,len(jsonObj)):
                self._encodeContainer(jsonObj[k])

        elif isinstance(jsonObj, float):
            self._binaryStream.writeUByte(self._floatStart)
            self._binaryStream.writeFloat(jsonObj)
            #print "float " + str(jsonObj)
        elif isinstance(jsonObj, basestring):
            self._binaryStream.writeUByte(self._stringStart)
            self._binaryStream.writeString(jsonObj)
            #print "string " + jsonObj
        elif isinstance(jsonObj, long):
            self._binaryStream.writeUByte(self._longStart)
            self._binaryStream.writeLong(jsonObj)
            #print "int " + str(jsonObj)
        elif isinstance(jsonObj, int):
            if jsonObj >= 0x7FFFFFFF:
                self._binaryStream.writeUByte(self._longStart)
                self._binaryStream.writeLong(jsonObj)
            else:
                self._binaryStream.writeUByte(self._intStart)
                self._binaryStream.writeInt(jsonObj)

            #print "int " + str(jsonObj)
        

        
        
    _output=""
    #=========================================
    def decode(self,bytes):
        self._binaryStream = ByteStreamReader()
        self._binaryStream._array = bytes
        startByte = self._binaryStream.readUByte() #read our keystone byte
        flagsByte = self._binaryStream.readUByte() #read our flags
        #print hex(startByte)
        self._decodeContainer()

        return self._output
    #=========================================
    def _decodeContainer(self):
        if self._binaryStream.eos():return
        topByte = self._binaryStream.readUByte()
        #print hex(topByte)
        ctrType = topByte & 0xF0
        ctrLen = topByte & 0x0F
        
        
        if ctrType == self._dictStart:
            self._output+="{"
            
            numItesm = self._binaryStream.readUShort()
            for i in range(numItesm):
                key = self._binaryStream.readString()
                self._output+="\"" + key + "\":"
                self._decodeContainer()
                self._output+=","
            self._output=self._output[0:-1] + "}"

        elif ctrType == self._arrayStart:
            numItesm = self._binaryStream.readUByte()
            self._output+="["
            for i in range(numItesm):
                self._decodeContainer()
                self._output+=","
            self._output=self._output[0:-1] + "]"

        elif ctrType == self._floatStart:
            val = self._binaryStream.readFloat()
            self._output+=str(val)
        elif ctrType == self._intStart:
            val = self._binaryStream.readInt()
            self._output+=str(val)
        elif ctrType == self._stringStart:
            val = self._binaryStream.readString()
            self._output+="\"" + str(val) + "\""
        elif ctrType == self._longStart:
            val = self._binaryStream.readLong()
            self._output+=(val)
    
       
#=========================================
def decodeJSON(srcData, outFile,):

    jsdata=[]
    with open(inFile,'rb') as f: 
        #read the file here
        jsdata = f.read()
        f.close()

    #is this a binary file or a text file?
    #print str(int(jsdata[0]))
    if jsdata[0] != chr(0x1A): #we're a text file
        #parse the JSON object
        jsonObj = None
        try:
            jsonObj = json.loads(jsdata)
        except ValueError as ve:
            print  "Error decoding json object:" + str(ve)
        except Exception as e:
            print "Error decoding json object:" + str(sys.exc_info()[0])
            return
        

        #is there a 'transpose' flag on this object?
        if not "^" in jsonObj.keys():
            return #nothing to do if we're text, and not transposed..

        TransposeJSON().decode(jsonObj)
         #do some extra packing here....
        post =encodeJSONObjToText(jsonObj)

        fl = open(outFile,'w')
        fl.write(post);
        fl.close();
    else:
        bjson = BinaryJSON()
        binDat = bjson.decode(jsdata)

        fl = open(outFile,'w')
        fl.write(binDat);
        fl.close();


    
#=========================================
def encodeJSONObjToText(jsonObj):
    post = json.JSONEncoder().encode(jsonObj)

    #note these values are explict based upon how Python's encoder spits out things
    post = post.replace("\": ","\":")
    post = post.replace(", \"",",\"")
    post = post.replace("\", ","\",")
    post = post.replace("], ","],")
    post = post.replace(", [",",[")
    post = post.replace("], [","],[")

    post = post.replace("}, ","},")
    post = post.replace(", {",",{")
    post = post.replace("}, {","},{")

    return post

#=========================================
def encodeJSON(inFile,outFile, dataTransposeMode,doBinPack):

    jsdata=[]
    with open(inFile,'r') as f: 
        #read the file here
        jsdata = f.read()
        f.close()


    #parse the JSON object
    jsonObj = None
    try:
        jsonObj = json.loads(jsdata)
    except ValueError as ve:
        print  "Error decoding json object:" + str(ve)
    except Exception as e:
        print "Error decoding json object:" + str(sys.exc_info()[0])
        return

    #pack the source object to minimized string
    post = ""
    
    if dataTransposeMode>0:
        TransposeJSON().encode(jsonObj,dataTransposeMode)#note, this will modify the jsonOBJ

    if not doBinPack:

        #do some extra packing here....
        post =encodeJSONObjToText(jsonObj)

        fl = open(outFile,'w')
        fl.write(post);
        fl.close();
    else:
        #print jsonObj
        bjson = BinaryJSON()
        binDat = bjson.encode(jsonObj)

        fl = open(outFile,'wb')
        fl.write(binDat);
        fl.close();

#======================================
def compare(listA,listB):
    assert len(listA)==len(listB), "lengths wrong"
    for i in range(len(listA)):
        assert listA[i] == listB[i], "incorrect values at index " + str(i)

#======================================
if __name__ == '__main__':

    mode=True #encoding
    doBinaryFormat=False
    dataTransposeMode=0 # 0 = none, 1 = non recoverable, 2 = recoverable

    if len(sys.argv) <3:
        print "Usage : xfjson.py <options> infile outfile"
        print "\t -t : do data transpose, no reversal"
        print "\t -tr : do data transpose, allow reversal"
        print "\t -b : output binary format (compressor only)"
        print "\t -d : decompress"
        sys.exit(1)

    for i in range(1,len(sys.argv)):
        if sys.argv[i] == "-d":
            mode = False
        elif sys.argv[i] == "-b":
            doBinaryFormat = True
        elif sys.argv[i] == "-t":
            dataTransposeMode = 1
        elif sys.argv[i] == "-tr":
            dataTransposeMode = 2
            

    #find the first param that doesn't have a "-" in front.
    paramPos = 1
    for paramPos in range(1,len(sys.argv)):
        if sys.argv[paramPos][0] != "-":
            break


    inFile = sys.argv[paramPos]
    outFile = sys.argv[paramPos+1]
    
    
    if mode == True:
        data = encodeJSON(inFile,outFile,dataTransposeMode,doBinaryFormat)
    else:
        data = decodeJSON(inFile,outFile)