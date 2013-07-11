
==description==

This project will fetch generate a HAR file for a given online URL, and then provide an estimated cost for it

fetchHAR.py will fetch/generate a HAR file from either HTTP Archive, or PhantomJS
calcHARCosts.py will read in a specific HAR file, # of daily users, and estimated cost-per-gig to report to you a breakdown of how much the site costs to distribute.

==setup notes==

IF you plan to use phantomJS to generate HAR files, then you must add phantomJS here : http://phantomjs.org/download.html
place under "./phantomJS" (such that ./phantomJS/phantomjs.exe is the correct path to the executable)


For the ability to fetch from HTTPArchive, you'll need BeautifulSoup locaed in the root folder
http://www.crummy.com/software/BeautifulSoup/

==USAGE==

1. python fetchHAR.py html5rocks.com ./H5R.HAR
2. Get estimated daily visit count (1647259)
3. Get estimated cost-per-gig transferred (0.12 cents)
4. python calcHARCost.py ./H5R.HAR -gigcost 0.12 -dailyusers 1647259

results : 
Site : ./H5R.HAR
Est. # Users : 1647259
Est. $ / gig : 0.12
Assets: cost per year
        audio: $0 (0 bytes)
        audio.gz: $0 (0 bytes)
        img: $7415 (110358 bytes)
        img.gz: $0 (0 bytes)
        misc: $0 (0 bytes)
        misc.gz: $0 (0 bytes)
        plugin: $0 (0 bytes)
        plugin.gz: $0 (0 bytes)
        text: $0 (0 bytes)
        text.gz: $9606 (142972 bytes)
        video: $0 (0 bytes)
        video.gz: $0 (0 bytes)
Total size : 253330 bytes
Total cost : $17021