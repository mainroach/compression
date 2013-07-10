
==description==

This project will fetch generate a HAR file for a given online URL, and then provide an estimated cost for it

fetchHAR.py will fetch/generate a HAR file from either HTTP Archive, or PhantomJS
calcHARCosts.py will read in a specific HAR file, # of daily users, and estimated cost-per-gig to report to you a breakdown of how much the site costs to distribute.

==setup notes==

you can add phantomJS here : http://phantomjs.org/download.html
place under "./phantomJS"

Note that PhantomJS, as well as 'chrome specific HAR generation' will require Node.js to be installed and valid on your machine.

For the ability to fetch from HTTPArchive, you'll need BeautifulSoup locaed in the root folder
http://www.crummy.com/software/BeautifulSoup/


