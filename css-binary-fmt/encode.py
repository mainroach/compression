
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
import subprocess
import os
import os.path
import sys
import math
import struct
import shutil

import tinycss


from bitStream import BitStream
import byteStream
import fibcodes

'''
	Some requirements
	* Built against a window.document.styles list from Chrome; needs to stay in sync,
		So don't include values that aren't matched to it!
	 
	Doesn't currently work
	* Unit typing is non-existant during reconstruction (px, em, %)

	Suggested improvements
	* Should allow a mode to list singular properties inline, rather than in the table?
	* Functions should not be inline, rather they should generate some op-codes at the start of the file
		that will fill in a slot in the string table with a reference.
	* We should have a variable bit-rate for variable indexes
		The decoder can keep a count of how many times a variable has been seen, and increase the bit rate as neede
		What if we re-sorted the variable table by frequency, and used huff-codes in the byte-stream instead? 
			How would we know what type of a variable it is?
	* Should have some sort of versioning bits in the header


	Format
	*Header data
	* 2 bits - numeric control [0=byte,1=short,2=int, 3=float]
	* 16 bits - num Declaraion strings
	* 16 bits - num Property strings
	* 16 bits - num value strings 
	* 16 bits - num value numbers
	*Variable tables
	* [xx bits] - declaration string table (strings written as [len(short)][chars(byte)])
	* [xx bits] - property string table 
	* [xx bits] - value strings table
	* [xx bits] - value numbers table 
				- values written based upon the numeric control above
	*Symbol stream, 16 bit function codes followed by data
	* fcn : 0xFFFF 0xXX : fcn will always be 0xFFFF, followed by a 8 bit pointer to the decl table
	* property single input : 0xXXXX 0xYY : 16 bits pointing to the static property table, 
											8 bits pointing to the variable table, variables are all offset
	* property multi input : 0xXXXX 0xYY [0xZZ ..]: 16 bits pointing to the static property table, 
													8 bits for number of inputs
													array of bytes pointing to variable table

'''
#===================================
lut_declNames={}
declNameCount=0

lut_propNames={}
propNamesCount=0

lut_numericValues={}
numericValuesCount=0

lut_stringValues={}
stringValuesCount=0

UNDEF_OBJ = 0x0
DECL_OBJ = 0x1
PROP_OBJ = 0x2
NUMERIC_OBJ = 0x3
STRING_OBJ = 0x4
FCN_OBJ = 0x5

DBG_PRINT = False
gEncodedNumericType = 0 #[byte, short, int, float]
gMaxNumericVal = 128
gFunctions = []

#===================================
def giveDeclID(declVal):
	global declNameCount
	global lut_declNames

	if not declVal in lut_declNames:
		lut_declNames[declVal] =declNameCount		
		declNameCount+=1
	
	return lut_declNames[declVal]
#===================================
def giveNameID(declVal):
	global propNamesCount
	global lut_propNames

	if not declVal in lut_propNames:
		lut_propNames[declVal] =propNamesCount		
		propNamesCount+=1
	
	return lut_propNames[declVal]

#===================================
def giveNumericID(declVal):
	global numericValuesCount
	global lut_numericValues

	if not declVal in lut_numericValues:
		lut_numericValues[declVal] =numericValuesCount		
		numericValuesCount+=1
	
	return lut_numericValues[declVal]

#===================================
def giveStringID(declVal):
	global stringValuesCount
	global lut_stringValues

	if not declVal in lut_stringValues:
		lut_stringValues[declVal] =stringValuesCount		
		stringValuesCount+=1
	
	return lut_stringValues[declVal]
#===================================
def parseContainerParams(containerObj):
	
	#CLM would be nice to include a recursive version for this
	#But right now, just enumerate it as a string, and bail out.
	parms=[0,1]
	parms[0] = giveStringID(containerObj.as_css())
	parms[1] = STRING_OBJ
	
	return parms
	
#===================================
def parseToken(va):
	global gEncodedNumericType
	global gMaxNumericVal
	val = [0,1]
	#http://pythonhosted.org/tinycss/parsing.html#tinycss.token_data.Token
	if va.type == "DIMENSION":#An integer or number followed immediately by an identifier (the unit). Eg: 12px
		val[0] = giveNumericID(va.value)
		val[1] = NUMERIC_OBJ
		#va.unit == "px" / em / dpi

		if va.value > gMaxNumericVal:
			gMaxNumericVal = va.value
			if gMaxNumericVal >= 0xFFFF:
				gEncodedNumericType=2
			elif gMaxNumericVal >= 0xFF:
				gEncodedNumericType=1
				

	elif va.type == "INTEGER": #An integer with an optional + or - sign
		val[0] = giveNumericID(va.value)
		val[1] = NUMERIC_OBJ

		if va.value > gMaxNumericVal:
			gMaxNumericVal = va.value
			if gMaxNumericVal >= 0xFFFF:
				gEncodedNumericType=2
			elif gMaxNumericVal >= 0xFF:
				gEncodedNumericType=1
				
	
	elif va.type == "NUMBER":#A non-integer number with an optional + or - sign
		val[0] = giveNumericID(va.value)
		val[1] = NUMERIC_OBJ
		
		gEncodedNumericType=3
		gMaxNumericVal = 999999999

	elif va.type == "PERCENTAGE":#An integer or number followed immediately by %
		val[0] = giveNumericID(va.value)
		val[1] = NUMERIC_OBJ

		#note, percentages tend to have floating point data...
		if int(va.value) != va.value:
			gEncodedNumericType=3
			gMaxNumericVal = 999999999
		else:
			if va.value > gMaxNumericVal:
				gMaxNumericVal = va.value
				if gMaxNumericVal >= 0xFFFF:
					gEncodedNumericType=2
					print 'changed'
				elif gMaxNumericVal >= 0xFF:
					gEncodedNumericType=1
					print 'changed'
		#va.unit == "%"
	elif va.type == "HASH": # # followed by a name : #FF88
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ
	elif va.type == "UNICODE-RANGE": # U+ followed by two hexidecimal unicode points Eg: U+20-00FF
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ

	elif va.type == "IDENT": #a name that does not start with a digit
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ
	elif va.type == "ATKEYWORD": #@ follwed by identifier
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ
	elif va.type == "URI": #eg url(foo) content may or may not be quoted
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ
	elif va.type == "STRING":#A string, quoted with " or '
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ
	
	elif va.type == "DELIM":#A single character not matched in another token. Eg: ,
		val[0] = giveStringID(va.value)
		val[1] = STRING_OBJ

	#else if va.type == "S":# sequence of white space
		
	#else if va.type == ":":
	#else if va.type == ";":
	else: #uhhhhh, mayble like an enum or somethign?
		val[0] = giveStringID(va.as_css())
		val[1] = STRING_OBJ
	
	if DBG_PRINT: print "  " + str(va.value) + "("+ str(val[0]) +")"
	return val



#===================================
def subParsePropValue(fcnSet, valueList):

	for va in valueList:
		if va.is_container: #we're  a container token or function token
			parm=parseContainerParams(va)
			fcnSet.append(parm)
		else:
			#try to clean up some input
			if(va.as_css() == " "):
				continue
			parm = parseToken(va)
			fcnSet.append(parm)
	

#===================================
def binarizeCSS(filename):
	global gFunctions
	parser = tinycss.make_parser('page3')
	stylesheet = parser.parse_stylesheet_file(filename)
	for rle in stylesheet.rules:
		if not hasattr(rle, 'declarations'): continue

		fcnSet=[]
		declVal = rle.selector.as_css()
		dclid = giveDeclID(declVal)
		
		fcnSet.append([0xFFFF,UNDEF_OBJ])#lddcl
		fcnSet.append([dclid,DECL_OBJ])
		
		gFunctions.append(fcnSet)
		if DBG_PRINT: print "LDDCL " + str(dclid)  + "(" + declVal+")" + str(len(rle.declarations))

		
		for prop in rle.declarations:
			propSet=[]
			#print "-" + prop.name
			#make a tree-style structure to count properties used as well
			propID = giveNameID(prop.name)

			if DBG_PRINT: print " " + prop.name + "(" +str(propID)+ ")" + str(len(prop.value))
			
			propSet.append([propID,PROP_OBJ])

			#if there's multiple inputs, then write a 'more' byte
			pVal = len(propSet)
			if len(prop.value) > 2:
				propSet.append([0,UNDEF_OBJ])

			#write the values to stream
			subParsePropValue(propSet, prop.value)

			#now go back and set how many we acutally wrote
			pCount = len(propSet)-(pVal+1)
			if pCount > 1:
				pCount |= 0x80
			
				propSet[pVal][0]=pCount


			gFunctions.append(propSet)


#===================================
def writeBinCSS(outfile):
	

	fileStream = byteStream.ByteStreamWriter()
	#write some control bits


	#write header
	fileStream.writeShort(len(lut_declNames.keys()))
	fileStream.writeShort(len(lut_propNames.keys()))
	fileStream.writeShort(len(lut_stringValues.keys()))
	fileStream.writeShort(len(lut_numericValues.keys()))

	#first, let's write our vTable
	#we need to know what area of variable block our pointer is looking at, so we need to stagger it
	declStart = 0
	propStart = len(lut_declNames.keys())
	stringStart = propStart + len(lut_propNames.keys())
	numberStart = stringStart + len(lut_stringValues.keys())

	
	for k in sorted(lut_declNames, key=lut_declNames.get, reverse=False):
		fileStream.writeString(k)

	for k in sorted(lut_propNames, key=lut_propNames.get, reverse=False):
		fileStream.writeString(k)

	for k in sorted(lut_stringValues, key=lut_stringValues.get, reverse=False):
		fileStream.writeString(k)

	for k in sorted(lut_numericValues, key=lut_numericValues.get, reverse=False):
		if gEncodedNumericType == 0:
			print k
			fileStream.writeByte(k)
		elif gEncodedNumericType ==1 :
			fileStream.writeShort(k)
		elif gEncodedNumericType ==2 :
			fileStream.writeInt(k)
		elif gEncodedNumericType ==3 :
			fileStream.writeFloat(k)



	#Now, let's write our byte stream referencing that VTable
	#first generate all our fib codes we'll use.
	fibCodes=fibcodes.genFib3Codes(len(lut_declNames.keys()) + len(lut_propNames.keys()) + len(lut_stringValues.keys()) + len(lut_numericValues.keys()))

	dict_size=1
	numBitsForDictSize = int(math.floor(math.log(dict_size,2)+1))
	bres = BitStream()
	#preallocate a 'used' table to the max number of variables used
	usedTable={}

	for fcn in gFunctions:
		#fileStream._array += gOutStream._array
		if(fcn[0][0] == 0xFFFF):
			bres.addSubInt32(fcn[0][0],16)
			bres.addSubInt32(fcn[1][0],8)
		else:		
			for qq in range(0, len(fcn)):
				propPair = fcn[qq]
				
				if propPair[1] == PROP_OBJ:
					bres.addSubInt32(propPair[0] + propStart,16)

				elif propPair[1] == NUMERIC_OBJ:

					v = propPair[0] + numberStart #basic value

					uCode = fibCodes[v][0]
					uCodeLen = fibCodes[v][1]

					bres.addSubInt32(uCode,uCodeLen)

				elif propPair[1] == STRING_OBJ:
					v = propPair[0] + stringStart

					uCode = fibCodes[v][0]
					uCodeLen = fibCodes[v][1]

					bres.addSubInt32(uCode,uCodeLen)

				elif propPair[1] == UNDEF_OBJ:
					bres.addSubInt32(propPair[0],8)

	#print len(bres.toByteArray())
	if DBG_PRINT:
		print fcn

	return [fileStream._array,bres.toByteArray()]
				

#=====================================
def gzipCompress(inFile,outFile,level=9):
    shutil.copyfile(inFile, outFile)
    
    if "darwin" in sys.platform:
        args = "gzip"
        args += " -f"
        args += " -" + str(level) #6 is default for browsers
        args += " " + outFile
    else:
        args = "gzip.exe"
        args += " -f"
        args += " -" + str(level) #6 is default for browsers
        args += " " + outFile
    
    os.system(args)

    return os.path.getsize( outFile+ ".gz")
#======================================
def gzipCompressData(data,outFile,level=9):
    f = open("./dat.org","wb")
    f.write(data)
    f.close()

    size_gz2 = gzipCompress("./dat.org",outFile)
    return size_gz2


#===================================
if __name__ == "__main__":


	infile = sys.argv[1]
	outfile = sys.argv[2]
	
	binarizeCSS(infile)
	print "---------------"

	print "declNames:" + str(len(lut_declNames.keys()))
	print "propNames:" + str(len(lut_propNames.keys()))
	print "strings:" + str(len(lut_stringValues.keys()))
	print "numbers:" + str(len(lut_numericValues.keys()))
	print "# mode: " + str(gEncodedNumericType)
	
	
	#print "total:" + str(numericValuesCount + stringValuesCount + declNameCount + (propNamesCount - len(propNameList)))
	
	outData = writeBinCSS(outfile)


	f = open(outfile,"wb")
	f.write(outData[0])
	f.write(outData[1])
	f.close()
	

	f = open(infile,"rb")
	srcSize = len(f.read())
	f.close()
	print "src: " + str(srcSize)
	print "src.gz: " + str(gzipCompress(infile,"./tmp.tmp"))
	print ".bin : " + str(len(outData[0]) + len(outData[1]))
	print ".bin.gz : " + str(gzipCompress(outfile,"./tmp.tmp"))
	print "==============="
	#testDecomp(outfile)

