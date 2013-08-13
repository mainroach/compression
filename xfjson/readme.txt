======LICENSE
Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
#limitations under the License.

=======WHAT IS THIS CODE

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



You can find the article detailing this structure at @ http://mainroach.blogspot.com/2013/08/json-compression-transpose-binary.html