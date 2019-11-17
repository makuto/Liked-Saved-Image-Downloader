#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpclient
import tornado.gen

import json
import multiprocessing
import os
import random
import shutil
import threading
import webbrowser

import utilities
import settings
import redditUserImageScraper
import LikedSavedDatabase

# Require a username and password in order to use the web interface. See ReadMe.org for details.
#enable_authentication = False
enable_authentication = True

if enable_authentication:
    import PasswordManager

# List of valid user ids (used to compare user cookie)
authenticated_users = []

# If "next" isn't specified from login, redirect here after login instead
landingPage = "/"

class SessionData:
    def __init__(self):
        # Just in case, because tornado is multithreaded
        self.lock = threading.Lock()
        
        self.randomHistory = []
        self.randomHistoryIndex = -1
        self.favorites = []
        self.favoritesIndex = 0
        self.currentImage = None
        self.randomImageFilter = ''
        self.filteredImagesCache = []
        
        self.currentDirectoryPath = ''
        self.currentDirectoryCache = []
        self.directoryFilter = ''

    def acquire(self):
        self.lock.acquire()
    def release(self):
        self.lock.release()

# user id : session data
userSessionData = {}

videoExtensions = ('.mp4', '.webm')
supportedExtensions = ('.gif', '.jpg', '.jpeg', '.png', '.mp4', '.webm')

savedImagesCache = []
def generateSavedImagesCache(outputDir):
    global savedImagesCache
    # Clear cache in case already created
    savedImagesCache = []

    print('Creating content cache...')
    
    for root, dirs, files in os.walk(outputDir):
        for file in files:
            if file.endswith(supportedExtensions):
                savedImagesCache.append(os.path.join(root, file))

    print('Finished creating content cache ({} images/videos)'.format(len(savedImagesCache)))

def getRandomImage(filteredImagesCache=None, randomImageFilter=''):
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])

    if filteredImagesCache:
        randomImage = random.choice(filteredImagesCache)
    else:
        randomImage = random.choice(savedImagesCache)

    print('\tgetRandomImage(): Chose random image {} (filter {})'.format(randomImage, randomImageFilter))

    serverPath = utilities.outputPathToServerPath(randomImage)

    return randomImage, serverPath

#
# Tornado handlers
#

# See https://github.com/tornadoweb/tornado/blob/stable/demos/blog/blog.py
# https://www.tornadoweb.org/en/stable/guide/security.html

def login_get_current_user(handler):
    if enable_authentication:
        cookie = handler.get_secure_cookie("user")
        if cookie in authenticated_users:
            return cookie
        else:
            print("Bad/expired cookie received")
            return None
    else:
        return "authentication_disabled"

class AuthHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return login_get_current_user(self)
    
class LoginHandler(AuthHandler):
    def get(self):
        if not enable_authentication:
            self.redirect("/")
        else:
            if PasswordManager.havePasswordsBeenSet():
                self.render("templates/Login.html",
                            next=self.get_argument("next", landingPage),
                            xsrf_form_html=self.xsrf_form_html())
            else:
                # New password setup
                self.render("templates/LoginCreate.html",
                            next=self.get_argument("next", landingPage),
                            xsrf_form_html=self.xsrf_form_html())

    def post(self):
        global authenticated_users
        # Test password
        print("Attempting to authorize user {}...".format(self.get_argument("name")))
        if enable_authentication and PasswordManager.verify(self.get_argument("password")):
            # Generate new authenticated user session
            randomGenerator = random.SystemRandom()
            cookieSecret = str(randomGenerator.getrandbits(128))
            authenticated_user = self.get_argument("name") + "_" + cookieSecret
            authenticated_user = authenticated_user.encode()
            authenticated_users.append(authenticated_user)
            
            # Set the cookie on the user's side
            self.set_secure_cookie("user", authenticated_user)
            
            print("Authenticated user {}".format(self.get_argument("name")))
            
            # Let them in
            self.redirect(self.get_argument("next", landingPage))
        else:
            print("Refused user {} (password doesn't match any in database)".format(self.get_argument("name")))
            self.redirect("/login")
            
class LogoutHandler(AuthHandler):
    @tornado.web.authenticated
    def get(self):
        global authenticated_users
        
        if enable_authentication:
            print("User {} logging out".format(self.current_user))
            if self.current_user in authenticated_users:
                authenticated_users.remove(self.current_user)
            self.redirect("/login")
        else:
            self.redirect("/")

class SetPasswordHandler(AuthHandler):
    def get(self):
        pass

    def post(self):
        if not enable_authentication:
            self.redirect("/")
        else:
            print("Attempting to set password")
            if PasswordManager.havePasswordsBeenSet():
                print("Rejected: Password has already been set!")
            elif self.get_argument("password") != self.get_argument("password_verify"):
                print("Rejected: password doesn't match verify field!")
            else:
                PasswordManager.createPassword(self.get_argument("password"))
                print("Success: Set password")

            self.redirect("/login")

class AuthedStaticHandler(tornado.web.StaticFileHandler):
    def get_current_user(self):
        return login_get_current_user(self)
    
    @tornado.web.authenticated
    def prepare(self):
        pass

class HomeHandler(AuthHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('webInterface/index.html')

def settingsToHtmlForm():
    settingsInputs = []

    for sectionSettingsPair in settings.settingsStructure:
        settingsInputs.append('<h2>{}</h2>'.format(sectionSettingsPair[0]))

        for sectionOption in sectionSettingsPair[1]:
            option = None
            optionComment = ''
            if type(sectionOption) == tuple:
                option = sectionOption[0]
                optionComment = '<p class="optionComment">{}</p>'.format(sectionOption[1])
            else:
                option = sectionOption
                
            if type(settings.settings[option]) == bool:
                settingsInputs.append('''<label for="{option}">{optionName}</label>
                                     <input type="checkbox" id="{option}" name="{option}" value="{optionValue}" {checkedState} />{comment}
                                     <br />'''
                                      .format(option=option, optionName=option.replace('_', ' '),
                                              comment=optionComment,
                                              checkedState=('checked' if settings.settings[option] else ''),
                                              optionValue=('1' if settings.settings[option] else '0')))
                
            elif type(settings.settings[option]) == int:
                settingsInputs.append('''<label for="{option}">{optionName}</label>
                                     <input type="number" id="{option}" name="{option}" value="{optionValue}" />{comment}
                                     <br />'''
                                      .format(option=option, optionName=option.replace('_', ' '), comment=optionComment,
                                              optionValue=settings.settings[option]))
                
            elif type(settings.settings[option]) == str:
                settingsInputs.append('''<label for="{option}">{optionName}</label>
                                     <input type="{type}" id="{option}" name="{option}" value="{optionValue}" />{comment}
                                     <br />'''
                                      .format(option=option, optionName=option.replace('_', ' '),
                                              comment=optionComment, optionValue=settings.settings[option],
                                              type=('password' if 'secret' in option.lower() or 'password' in option.lower() else 'text')))

    return ''.join(settingsInputs)

class SettingsHandler(AuthHandler):
    def doSettings(self, afterSubmit):
        htmlSettingsForm = settingsToHtmlForm()
        settingsFilename = settings.getSettingsFilename()

        self.render("templates/Settings.html",
                    status_html=('<p><b>Settings updated</b></p>' if afterSubmit else ''),
                    settings_filename=settingsFilename,
                    settings_form_html=htmlSettingsForm,
                    xsrf_form_html=self.xsrf_form_html())

    @tornado.web.authenticated
    def get(self):
        self.doSettings(False)

    @tornado.web.authenticated
    def post(self):
        currentOutputDir = settings.settings['Output_dir']
        
        print('Received new settings')
        
        for option in settings.settings:
            newValue = self.get_argument(option, None)
            if not newValue:
                # It's okay if it's a boolean because POST doesn't send unchecked checkboxes
                # This means the user set the value to false
                if type(settings.settings[option]) == bool:
                    settings.settings[option] = False
                else:
                    print('Warning: Option {} unset! The settingsStructure might be out of sync.'
                          '\n\tIgnore this if the field is intentionally empty'.format(option))
            else:
                # All false bools are handed in the above if block, so we know they're true here
                if type(settings.settings[option]) == bool:
                    newValue = True
                elif type(settings.settings[option]) == int:
                    newValue = int(newValue)
                
                settings.settings[option] = newValue
                # print('\tSet {} = {}'.format(option, newValue))

        # Write out the new settings
        settings.writeServerSettings()
        
        # Respond with a settings page saying we've updated the settings
        self.doSettings(True)

        # Refresh the cache in case the output directory changed
        if currentOutputDir != settings.settings['Output_dir']:
            generateSavedImagesCache(settings.settings['Output_dir'])
            

class RandomImageBrowserWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    def cacheFilteredImages(self):
        # Clear the cache
        self.sessionData.filteredImagesCache = []

        if not self.sessionData.randomImageFilter:
            return

        randomImageFilterLower = self.sessionData.randomImageFilter.lower()
    
        for imagePath in savedImagesCache:
            if randomImageFilterLower in imagePath.lower():
                self.sessionData.filteredImagesCache.append(imagePath)

        print('\tFiltered images with "{}"; {} images matching filter'
              .format(self.sessionData.randomImageFilter,
                      len(self.sessionData.filteredImagesCache)))

    def changeCurrentDirectory(self, newDirectory):
        self.sessionData.currentDirectoryPath = newDirectory
        dirList = os.listdir(self.sessionData.currentDirectoryPath)
        
        filteredDirList = []
        for fileOrDir in dirList:
            # The script spits out a lot of .json files the user probably doesn't want to see
            if (not fileOrDir.endswith('.json')
                and (not self.sessionData.directoryFilter
                     or self.sessionData.directoryFilter.lower() in fileOrDir.lower())):
                filteredDirList.append(fileOrDir)
                
        self.sessionData.currentDirectoryCache = sorted(filteredDirList)

    def open(self):
        global userSessionData
        currentUser = login_get_current_user(self)
        if not currentUser:
            # Failed authorization
            return None
        
        self.connections.add(self)
        
        if currentUser not in userSessionData:
            newSessionData = SessionData()
            userSessionData[currentUser] = newSessionData

        self.sessionData = userSessionData[currentUser]

        self.sessionData.acquire()
        # Set up the directory cache with the top-level output
        self.changeCurrentDirectory(settings.settings['Output_dir'])
        self.sessionData.release()
            
    def on_message(self, message):
        currentUser = login_get_current_user(self)
        if not currentUser:
            # Failed authorization
            return None
        
        print('RandomImageBrowserWebSocket: Received message ', message)
        parsedMessage = json.loads(message)
        command = parsedMessage['command']
        print('RandomImageBrowserWebSocket: Command ', command)
        action = ''

        self.sessionData.acquire()
        
        """
         Random Image Browser
        """
        
        if command == 'imageAddToFavorites':
            if self.sessionData.currentImage:
                self.sessionData.favorites.append(self.sessionData.currentImage)
                self.sessionData.favoritesIndex = len(self.sessionData.favorites) - 1
                LikedSavedDatabase.db.addFileToCollection(self.sessionData.currentImage[1], "Favorites")
                 
        if command == 'nextFavorite':
            self.sessionData.favoritesIndex += 1
            if self.sessionData.favoritesIndex >= 0 and self.sessionData.favoritesIndex < len(self.sessionData.favorites):
                action = 'setImage'
                fullImagePath, serverImagePath = self.sessionData.favorites[self.sessionData.favoritesIndex]
            else:
                self.sessionData.favoritesIndex = len(self.sessionData.favorites) - 1
                if len(self.sessionData.favorites):
                    action = 'setImage'
                    fullImagePath, serverImagePath = self.sessionData.favorites[self.sessionData.favoritesIndex]

        if command == 'previousFavorite' and len(self.sessionData.favorites):
            action = 'setImage'

            if self.sessionData.favoritesIndex > 0:
                self.sessionData.favoritesIndex -= 1
                
            fullImagePath, serverImagePath = self.sessionData.favorites[self.sessionData.favoritesIndex]

        if command == 'nextImage':
            action = 'setImage'

            if self.sessionData.randomHistoryIndex == -1 or self.sessionData.randomHistoryIndex >= len(self.sessionData.randomHistory) - 1:
                fullImagePath, serverImagePath = getRandomImage(self.sessionData.filteredImagesCache, self.sessionData.randomImageFilter)
                self.sessionData.randomHistory.append((fullImagePath, serverImagePath))
                self.sessionData.randomHistoryIndex = len(self.sessionData.randomHistory) - 1
            else:
                self.sessionData.randomHistoryIndex += 1
                fullImagePath, serverImagePath = self.sessionData.randomHistory[self.sessionData.randomHistoryIndex]

        if command == 'previousImage':
            action = 'setImage'

            if self.sessionData.randomHistoryIndex > 0:
                self.sessionData.randomHistoryIndex -= 1
                
            fullImagePath, serverImagePath = self.sessionData.randomHistory[self.sessionData.randomHistoryIndex]

        if command in ['nextImageInFolder', 'previousImageInFolder'] and len(self.sessionData.randomHistory):
            fullImagePath, serverImagePath = self.sessionData.currentImage
                
            folder = fullImagePath[:fullImagePath.rfind('/')]
            imagesInFolder = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(supportedExtensions):
                        imagesInFolder.append(os.path.join(root, file))
            utilities.sort_naturally(imagesInFolder)
            currentImageIndex = imagesInFolder.index(fullImagePath)
            if currentImageIndex >= 0:
                action = 'setImage'
                
                nextImageIndex = currentImageIndex + (1 if command == 'nextImageInFolder' else -1)
                if nextImageIndex == len(imagesInFolder):
                    nextImageIndex = 0
                if nextImageIndex < 0:
                    nextImageIndex = len(imagesInFolder) - 1
                    
                fullImagePath = imagesInFolder[nextImageIndex]
                serverImagePath = utilities.outputPathToServerPath(fullImagePath)

        if command == 'setFilter':
            newFilter = parsedMessage['filter']
            if newFilter != self.sessionData.randomImageFilter:
                self.sessionData.randomImageFilter = newFilter
                self.cacheFilteredImages()

        """
         Directory browser
        """

        if command == 'setDirectoryFilter':
            newFilter = parsedMessage['filter']
            if newFilter != self.sessionData.directoryFilter:
                self.sessionData.directoryFilter = newFilter
                # Refresh cache with new filter
                self.changeCurrentDirectory(self.sessionData.currentDirectoryPath)
                action = 'sendDirectory'

        if command == 'listCurrentDirectory':
            action = 'sendDirectory'

        if command == 'changeDirectory':
            # Reset the filter (chances are the user only wanted to filter at one level
            self.sessionData.directoryFilter = ''
            self.changeCurrentDirectory('{}/{}'.format(self.sessionData.currentDirectoryPath, parsedMessage['path']));
            action = 'sendDirectory'

        if command == 'directoryUp':
            # Don't allow going higher than output dir
            if self.sessionData.currentDirectoryPath != settings.settings['Output_dir']:
                upDirectory = (settings.settings['Output_dir']  +
                               self.sessionData.currentDirectoryPath[len(settings.settings['Output_dir'])
                                                         : self.sessionData.currentDirectoryPath.rfind('/')])
                # Reset the filter (chances are the user only wanted to filter at one level
                self.sessionData.directoryFilter = ''
                self.changeCurrentDirectory(upDirectory)
                action = 'sendDirectory'
            
        if command == 'directoryRoot':
            # Reset the filter (chances are the user only wanted to filter at one level
            self.sessionData.directoryFilter = ''
            self.changeCurrentDirectory(settings.settings['Output_dir'])
            action = 'sendDirectory'

        """
         Actions
        """

        # Only send a response if needed
        if action == 'setImage':
            # Stupid hack
            if serverImagePath.endswith(videoExtensions):
                action = 'setVideo'
                
            self.sessionData.currentImage = (fullImagePath, serverImagePath)
            responseMessage = ('{{"responseToCommand":"{}", "action":"{}", "fullImagePath":"{}", "serverImagePath":"{}"}}'
                               .format(command, action, fullImagePath, serverImagePath))
            self.write_message(responseMessage)

        if action == 'sendDirectory':
            directoryList = ''
            for path in self.sessionData.currentDirectoryCache:
                isSupportedFile = path.endswith(supportedExtensions)
                isFile = '.' in path
                if path.endswith(videoExtensions):
                    fileType = 'video'
                elif isSupportedFile:
                    fileType = 'image'
                elif isFile:
                    fileType = 'file'
                else:
                    fileType = 'dir'
                serverPath = 'output' + self.sessionData.currentDirectoryPath[len(settings.settings['Output_dir']):] + '/' + path
                directoryList += '{{"path":"{}", "type":"{}", "serverPath":"{}"}},'.format(path, fileType, serverPath)

            # Do directoryList[:-1] (yuck) to trim the final trailing comma because JSON doesn't like it
            responseMessage = ('{{"responseToCommand":"{}", "action":"{}", "directoryList":[{}]}}'
                               .format(command, action, directoryList[:-1]))
            self.write_message(responseMessage)

        self.sessionData.release()
    

    def on_close(self):
        self.connections.remove(self)

scriptPipeConnection = None
scriptProcess = None

def startScript():
    global scriptPipeConnection, scriptProcess
    
    # Script already running
    if scriptProcess and scriptProcess.is_alive():
        return
    
    scriptPipeConnection, childConnection = multiprocessing.Pipe()
    scriptProcess = multiprocessing.Process(target=redditUserImageScraper.runLikedSavedDownloader,
                                            args=(childConnection,))
    scriptProcess.start()

runScriptWebSocketConnections = set()
class RunScriptWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        if not login_get_current_user(self):
            return None
        
        global runScriptWebSocketConnections
        runScriptWebSocketConnections.add(self)

    def on_message(self, message):
        if not login_get_current_user(self):
            return None
        
        print('RunScriptWebSocket: Received message ', message)

        parsedMessage = json.loads(message)
        command = parsedMessage['command']

        print('RunScriptWebSocket: Command ', command)
        
        if command == 'runScript':
            if scriptProcess and scriptProcess.is_alive():
                print('RunScriptWebSocket: Script already running')
                responseMessage = ('{{"message":"{}", "action":"{}"}}'
                                   .format('Script already running\\n', 'printMessage'))
                self.write_message(responseMessage)
                
            else:
                print('RunScriptWebSocket: Starting script')

                startScript()
                
                responseMessage = ('{{"message":"{}", "action":"{}"}}'
                                   .format('Running script\\n', 'printMessage'))
                self.write_message(responseMessage)

    def on_close(self):
        global runScriptWebSocketConnections
        runScriptWebSocketConnections.remove(self)

def updateScriptStatus():
    global scriptPipeConnection
    # If no pipe or no data to receive from pipe, we're done
    # Poll() is non-blocking whereas recv is blocking
    try:
        if (not runScriptWebSocketConnections
            or not scriptPipeConnection
            or not scriptPipeConnection.poll()):
            return
    except OSError:
        scriptPipeConnection = None
        return

    pipeOutput = scriptPipeConnection.recv()
    if pipeOutput:
        responseMessage = ('{{"message":"{}", "action":"{}"}}'
                           .format(pipeOutput.replace('\n', '\\n').replace('\t', ''),
                                   'printMessage'))
        
        for client in runScriptWebSocketConnections:
            client.write_message(responseMessage)

        if redditUserImageScraper.scriptFinishedSentinel in pipeOutput:
            # Script finished; refresh image cache
            print('Refreshing cache due to script finishing')
            generateSavedImagesCache(settings.settings['Output_dir'])
            responseMessage = ('{{"action":"{}"}}'
                               .format('scriptFinished'))
            
            for client in runScriptWebSocketConnections:
                client.write_message(responseMessage)

            scriptPipeConnection.close()

#
# Startup
#

def make_app():
    # Each time the server starts up, invalidate all cookies
    randomGenerator = random.SystemRandom()
    cookieSecret = str(randomGenerator.getrandbits(128))
    
    return tornado.web.Application([
        # Home page
        (r'/', HomeHandler),
        
        # Login
        (r'/login', LoginHandler),
        (r'/logout', LogoutHandler),
        (r'/setPassword', SetPasswordHandler),
        
        # Configure the script
        (r'/settings', SettingsHandler),

        # Handles messages for run script
        (r'/runScriptWebSocket', RunScriptWebSocket),

        # Handles messages for randomImageBrowser
        (r'/randomImageBrowserWebSocket', RandomImageBrowserWebSocket),

        # Static files
        (r'/webInterface/(.*)', AuthedStaticHandler, {'path' : 'webInterface'}),
        # Don't change this "output" here without changing the other places as well
        (r'/output/(.*)', AuthedStaticHandler, {'path' : settings.settings['Output_dir']}),

        # Files served regardless of whether the user is authenticated. Only login page resources
        # should be in this folder, because anyone can see them
        (r'/webInterfaceNoAuth/(.*)', tornado.web.StaticFileHandler, {'path' : 'webInterfaceNoAuth'}),
    ],
                                   xsrf_cookies=True,
                                   cookie_secret=cookieSecret,
                                   login_url="/login")

if __name__ == '__main__':
    print('Loading settings...')
    settings.getSettings()

    print('Content output directory: ' + settings.settings['Output_dir'])
    if not settings.settings['Output_dir']:
        print('WARNING: No output directory specified! This will probably break things')
    
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])

    LikedSavedDatabase.initializeFromSettings(settings.settings)
    
    port = settings.settings['Port'] if settings.settings['Port'] else 8888
    print('\nStarting Content Collector Server on port {}...'.format(port))
    app = make_app()

    # Generating a self-signing certificate:
    # openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout certificates/server_jupyter_based.crt.key -out certificates/server_jupyter_based.crt.pem
    # (from https://jupyter-notebook.readthedocs.io/en/latest/public_server.html)
    # I then had to tell Firefox to trust this certificate even though it is self-signing (because
    # I want a free certificate for this non-serious project)
    useSSL = True
    if useSSL:
        if os.path.exists("certificates/liked_saved_server.crt.pem"):
            app.listen(port, ssl_options={"certfile":"certificates/liked_saved_server.crt.pem",
                                          "keyfile":"certificates/liked_saved_server.crt.key"})
        # For backwards compatibility
        elif os.path.exists("certificates/server_jupyter_based.crt.pem"):
            app.listen(port, ssl_options={"certfile":"certificates/server_jupyter_based.crt.pem",
                                          "keyfile":"certificates/server_jupyter_based.crt.key"})
        else:
            print('\n\tERROR: Certificates non-existent! Run ./Generate_Certificates.sh to create them')
    else:
        # Show the warning only if SSL is not enabled
        print('\n\tWARNING: Do NOT run this server on the internet (e.g. port-forwarded)'
          ' nor when\n\t connected to an insecure LAN! It is not protected against malicious use.\n')
        app.listen(port)

    if settings.settings['Launch_Browser_On_Startup']:
        browseUrl  ="{}://localhost:{}".format('https' if useSSL else 'http', port)
        print("Attempting to launch user's default browser to {}".format(browseUrl))
        webbrowser.open(browseUrl)

    ioLoop = tornado.ioloop.IOLoop.current()
    updateStatusCallback = tornado.ioloop.PeriodicCallback(updateScriptStatus, 100)
    updateStatusCallback.start()
    ioLoop.start()
