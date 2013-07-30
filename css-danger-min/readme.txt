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

This code attempts to identify 'dangerous' CSS minification optimizations to make, and present them to you.

Most minifiers exclude these optimizations entirely, simply because it could break someone’s css.

I view this as a throw-the-baby-out-with-the-bathwater methodology; There could be savings, if you’re willing to compromise. You don’t want the “Always Safest” minifier, you want the “Smallest producing minifier that breaks things that your site doesn’t use.” Which turns out to be a big difference. 

If we want to go to the extreme, we may find great savings by compromising, and building a CSS minifier chain that works this way, requires two things:
1. A minifier which will detect Safe, Semi-Safe and Not Safe optimizations
2. A feedback loop letting you know how those changes break your site.


The provided code will parse a given CSS block, and identify multiple semi-safe and unsafe targets for potential optimization. Effectively, it uses jsCSSP to parse the CSS block in JavaScript, and then per-block, identify if it’s a target for potential savings. For about 3 hours worth of work, I could semi-accurately identify over 500 potential optimizations for a CSS file from Google Plus; Most coming in the form of :

You can find the article detailing this structure at @ http://mainroach.blogspot.com/2013/07/css-compression-minifier-roulette.html