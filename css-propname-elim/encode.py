
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
import os.path
import sys
import math
import os, os.path
import os
import struct
import shutil
import operator

import tinycss

#======================================
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
def getGZipSize(data,level=9):
    f = open("./dat.org","wb")
    f.write(data)
    f.close()

    size_gz2 = gzipCompress("./dat.org","./tmp.tmp")
    return size_gz2
     
#===================================       
def genUsedNamesDictionary(data):

    propCountDictionary={}
    parser = tinycss.make_parser('page3')
    stylesheet = parser.parse_stylesheet_bytes(data)
    for rle in stylesheet.rules:
        if not hasattr(rle, 'declarations'): continue

        for prop in rle.declarations:
            #print prop.name
            if prop.name in propCountDictionary:
                propCountDictionary[prop.name] += 1
            else:
                propCountDictionary[prop.name] = 1

    
    valsDict = sorted(propCountDictionary.iteritems(), key=operator.itemgetter(1), reverse=True)

    sortedVals = []
    for k,v in valsDict:
        #print k
        sortedVals.append(k)

    
    return sortedVals


#===================================
def testVersion0(infile,browserStyleLUT):
    print ".Version0"
    '''
        This version tests the validity of mapping a set of CSS enumeration values to a specific browser's set
        This version will :
            1) Read in the source file
            2) Read the browser LUT file
            3) replace all the instancs in the source file with indexes to the LUT list
            4) report results
            
    '''
    f = open(infile,"r")
    dat = f.read()
    f.close()
    srcGZ=getGZipSize(dat)

    propTables = loadCSSLUT(browserStyleLUT)

    i = 0
    for i in range(len(propTables[1])):
        symb = propTables[1][i]
        dat = dat.replace(symb,"^" + str(i))

    finalGZ=getGZipSize(dat)
    
    finalBytesSaved = srcGZ - finalGZ
    print str(srcGZ) + " - " + str(len(dat)) + "->" + str(finalGZ) + " = " + str(finalBytesSaved) + "b " + str((1.0 - finalGZ / float(srcGZ))*100) + "% savings"



#===================================
def loadCSSLUT(lutFile):

    
    static_lut_PropNames={}
    static_PropNameList=[]
    f = open(lutFile,"r")
    dat = f.read()
    f.close()

    propCount = 0
    props = dat.split("\n")

    for p in props:
        string = ""
        for l in p:
            if l.isupper():
                string += "-" + l.lower()
            else:
                string += l

        static_lut_PropNames[string] = propCount
        static_PropNameList.append(string)
        propCount +=1
    
    print "===" + str(propCount)

    return [static_lut_PropNames,static_PropNameList]

#===================================
if __name__ == "__main__":

    infile = sys.argv[1]

    styleFile="styles_chrome.txt"
    if len(sys.argv)>2:
        styleFile= sys.argv[2]
    testVersion0(infile,styleFile)
    
    
    
    
    
    


