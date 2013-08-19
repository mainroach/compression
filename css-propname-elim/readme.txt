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

This code will create an enumerated matchng between the property names of a CSS file and a particular browser version, such that we remove the names in the CSS file, resulting in better compression.

The attached code will run the encoding process, and spit out a value detalining how much savings (post gzip) you'll get with this technique. To be clear, I have not provided the javascript implimentation of the decoder.

You can find the article detailing this structure at @ mainroach.blogspot.com


==usage:==
First, you can run 'get_browser_styles.html' in your favorite browser to get the enumerated property name set.
Some example ones have already been stored in the repo as "styles_chrome.txt" etc.

python encode.py ../data-sets/css/15k.css styles_chrome.txt

will print out how many bytes you'll save post-gzip with this technique.