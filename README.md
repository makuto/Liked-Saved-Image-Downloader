# Reddit User Image Scraper

Use this awesome Python 2 or 3 script to download
* Images
* Gifs
* Imgur Albums
* Comments
...which you've marked as Liked, Hearted, or Saved from
* Reddit
* Tumblr
...to disk!

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

`settings.txt` has several additional features. Read the comments to know how to use them.

**Alternatively,** use the Web Server Interface to configure the script. Follow instructions below to use the server.
![Web settings](/images/LikedSavedSettings.png)

## Web Server Interface

This repository includes a simple web server interface. Unlike the main script, the server is supported in Python 3 only.

To use it, install tornado via `pip3 install tornado` then run `python3 LikedSavedDownloaderServer.py`. The interface can be seen by visiting `http://localhost:8888` in any web browser.

**The web server is not secure in any way and should NOT be run on an insecure network!**

![Web interface](/images/LikedSavedBrowser.png)

## Issues

Feel free to create Issues on this repo if you need help. I'm friendly so don't be shy.