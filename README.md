# Reddit User Image Scraper

Use this awesome Python 2/3 script to download all of your reddit (*new:* Tumblr too!) saved and upvoted/liked images/imgur albums to disk.

The script will also write reddit saved comments to a .json file.

## Directions

Make sure you have PRAW, pytumblr, jsonpickle, and ImgurPython installed:
`pip install praw pytumblr ImgurPython jsonpickle`

1. Open `settings.txt`
2. Fill in your username and password
3. Set SHOULD_SOFT_RETRIEVE to False if you are sure you want to do this
4. Run the script: `python redditUserImageScraper.py`
5. Wait for a while
6. Check your output directory (the default is `output` relative to where you ran the script) for all your images!

If you want more images, set Reddit_Total_Requests and/or Tumblr_Total_Requests to a higher value. It's difficult to say how high to set it to get all of your images.

Not actually getting images downloaded, but seeing the console say it downloaded images? Make sure `SHOULD_SOFT_RETRIEVE=False` in `settings.txt`


## Issues

Feel free to create Issues on this repo if you need help. I'm a nice guy, so don't be shy.