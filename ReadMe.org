* Content Collector

Use this awesome tool to download
- Images
- Gifs
- Imgur Albums
- Videos
- Comments

...which you've marked as Liked, Hearted, or Saved from

- Reddit
- Tumblr

...to disk! You can then browse the results.

** Directions

*** 1. Clone this repository

#+BEGIN_SRC sh
git clone https://github.com/makuto/redditLikedSavedImageDownloader
#+END_SRC

*** 2. Install python dependencies

The following dependencies are required:

#+BEGIN_SRC sh
pip install praw pytumblr ImgurPython jsonpickle tornado youtube-dl git+https://github.com/ankeshanand/py-gfycat@master
#+END_SRC

You'll want to use Python 3, which for your environment may require you to specify ~pip3~ instead of just ~pip~.

**** Login-Protected Server

If you want to require the user to login before they can interact with the server, you must install passlib:

#+BEGIN_SRC sh
pip install passlib bcrypt argon2_cffi
#+END_SRC

*** 3. Generate SSL keys

#+BEGIN_SRC sh
cd redditLikedSavedImageDownloader/
./Generate_Certificates.sh
#+END_SRC

This step is only required if you want to use SSL, which ensures you have an encrypted connection to the server. You can disable this by opening ~LikedSavedDownloaderServer.py~ and setting ~useSSL = False~.

*** 4. Run the server

#+BEGIN_SRC sh
python3 LikedSavedDownloaderServer.py
#+END_SRC

*** 5.  Enter your account details and download the images

1. Open [[https://localhost:8888][localhost:8888]] in any web browser

If your web browser complains about the certificate, you may have to click ~Advanced~ and add the certificate as trustworthy, because you've signed the certificate and trust yourself :). If you want to get rid of this, you'll need to get a signing authority like ~LetsEncrypt~ to generate your certificate.

2. Use the Web Server Interface to configure the script:
[[file:images/LikedSavedSettings.png]]

3. Go to the Run Script page and click "Run Script"

4. Wait until the script finishes (it will say "Finished" at the bottom of the page)

5. Enjoy! Use Random Image Browser to jump to random images you've downloaded, or browse your output directory

**  Web Server Features

This repository includes a simple web server interface. Unlike the main script, the server is supported in Python 3 only.

The interface can be seen by visiting ~https://localhost:8888~ in any web browser.

*The web server is not secure in any way and should NOT be run on an insecure network!*

[[file:images/LikedSavedBrowser.png]]

*** Login-Authenticated Server

The script includes an option to require login before running the script, changing settings, or browsing downloaded content.

*I'm no expert, so use and trust at your own risk!* This security is essentially a cheap padlock which keeps honest people honest and undetermined intruders out.

It requires some additional setup:

**** 1. Enable it in ~LikedSavedDownloaderServer.py~

Open ~LikedSavedDownloaderServer.py~ and find ~enable_authentication~. Set it equal to ~True~.

**** 2. Create your account(s)

Rather than have a web-based registration process, you'll create each account manually. This is because this service is only designed for private use.

You'll use ~PasswordManager.py~ to generate a file ~passwords.txt~ with your hashed (and salted) passwords:

#+BEGIN_SRC sh
python3 PasswordManager.py "Your Password Here"
#+END_SRC

You can create multiple valid passwords, if desired.

If you want to reset all passwords, simply delete ~passwords.txt~.

**** 3. Restart your server

You should now see a Login page before being able to access any content.

Note that all login cookies will be invalidated each time you restart the server.

** Running the script only

1. Copy ~settings_template.txt~ into a new file called ~settings.txt~
2. Open ~settings.txt~
3. Fill in your username and password
4. Set ~SHOULD_SOFT_RETRIEVE~ to ~False~ if you are sure you want to do this
5. Run the script: ~python redditUserImageScraper.py~
6. Wait for a while
7. Check your output directory (the default is ~output~ relative to where you ran the script) for all your images!

If you want more images, set ~Reddit_Total_Requests~ and/or ~Tumblr_Total_Requests~ to a higher value. The maximum is 1000. Unfortunately, reddit does not allow you to get more than 1000 submissions of a single type (1000 liked, 1000 saved).

Not actually getting images downloaded, but seeing the console say it downloaded images? Make sure ~SHOULD_SOFT_RETRIEVE=False~ in ~settings.txt~

~settings.txt~ has several additional features. Read the comments to know how to use them.

** Issues

Feel free to create Issues on this repo if you need help. I'm friendly so don't be shy.

