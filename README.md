Reddit User Image Scraper
--------------------------

Use this shitty Python script I whipped up in an hour to download all of
your reddit saved and upvoted/liked images to disk.

Make sure you have PRAW installed:
`pip install praw`

1. Open `redditUserImageScraper.py`
2. Fill in your username and password
3. Set SHOULD_SOFT_RETRIEVE to False if you are sure you want to do this
4. Run the script: `python redditUserImageScraper.py`
5. Wait for a while

If you want more images, set TOTAL_REQUESTS to a higher value. It's difficult to say how high to set it to get all of your images.

Not actually getting images downloaded, but seeing the console say it downloaded images? Make sure `SHOULD_SOFT_RETRIEVE = False` in `redditUserImageScraper.py`

This script uses PRAW to talk to reddit and urllib to download images.

Note that the script will probably break once reddit no longer supports username password authentication and moves over to OAuth completely.
