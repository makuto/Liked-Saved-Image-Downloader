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

1. Make sure you have PRAW, pytumblr, jsonpickle, Tornado, and ImgurPython installed:
`pip install praw pytumblr ImgurPython jsonpickle tornado`
2. Run `python3 LikedSavedDownloaderServer.py`
3. Open [localhost:8888](http://localhost:8888) in any web browser
4. Use the Web Server Interface to configure the script:
![Web settings](/images/LikedSavedSettings.png)
5. Go to the Run Script page and click "Run Script"
6. Wait until the script finishes (it will say "Finished" at the bottom of the page)
7. Enjoy! Use Random Image Browser to jump to random images you've downloaded, or browse your output directory

## Web Server Features

This repository includes a simple web server interface. Unlike the main script, the server is supported in Python 3 only.

To use it, install tornado via `pip3 install tornado` then run `python3 LikedSavedDownloaderServer.py`. The interface can be seen by visiting `http://localhost:8888` in any web browser.

**The web server is not secure in any way and should NOT be run on an insecure network!**

![Web interface](/images/LikedSavedBrowser.png)

## Running the script only

1. Open `settings.txt`
2. Fill in your username and password
3. Set SHOULD_SOFT_RETRIEVE to False if you are sure you want to do this
4. Run the script: `python redditUserImageScraper.py`
5. Wait for a while
6. Check your output directory (the default is `output` relative to where you ran the script) for all your images!

If you want more images, set Reddit_Total_Requests and/or Tumblr_Total_Requests to a higher value. The maximum is 1000. Unfortunately, reddit does not allow you to get more than 1000 submissions of a single type (1000 liked, 1000 saved).

Not actually getting images downloaded, but seeing the console say it downloaded images? Make sure `SHOULD_SOFT_RETRIEVE=False` in `settings.txt`

`settings.txt` has several additional features. Read the comments to know how to use them.

## Issues

Feel free to create Issues on this repo if you need help. I'm friendly so don't be shy.