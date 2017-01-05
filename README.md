Reddit User Image Scraper
--------------------------

Use this ~~shitty~~ awesome Python 2 script I whipped up ~~in an hour~~ over a couple months of sporadic development to download all of your reddit saved and upvoted/liked images to disk.

Make sure you have PRAW installed:
`pip install praw`

1. Open `settings.txt`
2. Fill in your username and password
3. Set SHOULD_SOFT_RETRIEVE to False if you are sure you want to do this
4. Run the script: `python redditUserImageScraper.py`
5. Wait for a while
6. Check your output directory (the default is `output` relative to where you ran the script) for all your images!

If you want more images, set TOTAL_REQUESTS to a higher value. It's difficult to say how high to set it to get all of your images.

Not actually getting images downloaded, but seeing the console say it downloaded images? Make sure `SHOULD_SOFT_RETRIEVE=False` in `settings.txt`

This script uses PRAW to talk to reddit and urllib to download images.

Note that the script will probably break once reddit no longer supports username password authentication and moves over to OAuth completely. *UPDATE:* As of November 29, 2016, PRAW has been updated to version 4.0, which requires OAuth in order to access reddit.

Feel free to create Issues on this repo if you need help. I'm a nice guy, so don't be shy.