#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpclient
import tornado.gen

import os
import random
import shutil
import json
import multiprocessing

from utilities import sort_naturally
import settings
import redditUserImageScraper

videoExtensions = ('.mp4', '.webm')
supportedExtensions = ('.gif', '.jpg', '.jpeg', '.png', '.mp4', '.webm')

savedImagesCache = []
def generateSavedImagesCache(outputDir):
    global savedImagesCache
    # Clear cache in case already created
    savedImagesCache = []

    print('Creating Liked Saved cache...')
    
    for root, dirs, files in os.walk(outputDir):
        for file in files:
            if file.endswith(supportedExtensions):
                savedImagesCache.append(os.path.join(root, file))

    print('Finished creating Liked Saved cache ({} images/videos)'.format(len(savedImagesCache)))

def outputPathToServerPath(path):
    return 'output' + path.split(settings.settings['Output_dir'])[1]

def getRandomImage(filteredImagesCache=None, randomImageFilter=''):
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])

    if filteredImagesCache:
        randomImage = random.choice(filteredImagesCache)
    else:
        randomImage = random.choice(savedImagesCache)

    print('\tgetRandomImage(): Chose random image {} (filter {})'.format(randomImage, randomImageFilter))

    # Dear gods, forgive me, this is weird; trim the full output path
    serverPath = outputPathToServerPath(randomImage)

    return randomImage, serverPath

#
# Tornado handlers
#

class HomeHandler(tornado.web.RequestHandler):
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

class SettingsHandler(tornado.web.RequestHandler):
    def doSettings(self, afterSubmit):
        htmlSettingsForm = settingsToHtmlForm()
        settingsFilename = settings.getSettingsFilename()
        
        self.write('''<html>
                            <head>
                                  <link rel="stylesheet" type="text/css" href="webInterface/settings.css">
                                  <script type="text/javascript" src="webInterface/settings.js"></script>
                            </head>
                            <body>
                                  <h1>Liked Saved Downloader Settings</h1>
                                  <a href="/">Back to Homepage</a><br /><br />
                                  {}
                                  <p>Settings being read from {}</p>
                                  <form action="/settings" method="post">
                                       <input type="submit" value="Submit">
                                       {}
                                       <input type="submit" value="Submit">
                                  </form>
                            </body>
                      </html>'''
                   .format(('<p><b>Settings updated</b></p>' if afterSubmit else ''),
                           settingsFilename, htmlSettingsForm))
        
    def get(self):
        self.doSettings(False)
        
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
        self.filteredImagesCache = []

        if not self.randomImageFilter:
            return

        randomImageFilterLower = self.randomImageFilter.lower()
    
        for imagePath in savedImagesCache:
            if randomImageFilterLower in imagePath.lower():
                self.filteredImagesCache.append(imagePath)

        print('\tFiltered images with "{}"; {} images matching filter'
              .format(self.randomImageFilter, len(self.filteredImagesCache)))

    def open(self):
        self.connections.add(self)
        self.randomHistory = []
        self.randomHistoryIndex = -1
        self.favorites = []
        self.favoritesIndex = 0
        self.currentImage = None
        self.randomImageFilter = ''
        self.filteredImagesCache = []

    def on_message(self, message):
        print('RandomImageBrowserWebSocket: Received message ', message)
        parsedMessage = json.loads(message)
        command = parsedMessage['command']
        print('RandomImageBrowserWebSocket: Command ', command)
        action = ''

        if command == 'imageAddToFavorites':
            if self.currentImage:
                self.favorites.append(self.currentImage)
                self.favoritesIndex = len(self.favorites) - 1

        if command == 'nextFavorite':
            self.favoritesIndex += 1
            if self.favoritesIndex >= 0 and self.favoritesIndex < len(self.favorites):
                action = 'setImage'
                fullImagePath, serverImagePath = self.favorites[self.favoritesIndex]
            else:
                self.favoritesIndex = len(self.favorites) - 1
                if len(self.favorites):
                    action = 'setImage'
                    fullImagePath, serverImagePath = self.favorites[self.favoritesIndex]

        if command == 'previousFavorite' and len(self.favorites):
            action = 'setImage'

            if self.favoritesIndex > 0:
                self.favoritesIndex -= 1
                
            fullImagePath, serverImagePath = self.favorites[self.favoritesIndex]

        if command == 'nextImage':
            action = 'setImage'

            if self.randomHistoryIndex == -1 or self.randomHistoryIndex >= len(self.randomHistory) - 1:
                fullImagePath, serverImagePath = getRandomImage(self.filteredImagesCache, self.randomImageFilter)
                self.randomHistory.append((fullImagePath, serverImagePath))
                self.randomHistoryIndex = len(self.randomHistory) - 1
            else:
                self.randomHistoryIndex += 1
                fullImagePath, serverImagePath = self.randomHistory[self.randomHistoryIndex]

        if command == 'previousImage':
            action = 'setImage'

            if self.randomHistoryIndex > 0:
                self.randomHistoryIndex -= 1
                
            fullImagePath, serverImagePath = self.randomHistory[self.randomHistoryIndex]

        if command in ['nextImageInFolder', 'previousImageInFolder'] and len(self.randomHistory):
            fullImagePath, serverImagePath = self.currentImage
                
            folder = fullImagePath[:fullImagePath.rfind('/')]
            imagesInFolder = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(supportedExtensions):
                        imagesInFolder.append(os.path.join(root, file))
            sort_naturally(imagesInFolder)
            currentImageIndex = imagesInFolder.index(fullImagePath)
            if currentImageIndex >= 0:
                action = 'setImage'
                
                nextImageIndex = currentImageIndex + (1 if command == 'nextImageInFolder' else -1)
                if nextImageIndex == len(imagesInFolder):
                    nextImageIndex = 0
                if nextImageIndex < 0:
                    nextImageIndex = len(imagesInFolder) - 1
                    
                fullImagePath = imagesInFolder[nextImageIndex]
                serverImagePath = outputPathToServerPath(fullImagePath)

        if command == 'setFilter':
            newFilter = parsedMessage['filter']
            if newFilter != self.randomImageFilter:
                self.randomImageFilter = newFilter
                self.cacheFilteredImages()

        # Only send a response if needed
        if action == 'setImage':
            # Stupid hack
            if serverImagePath.endswith(videoExtensions):
                action = 'setVideo'
                
            self.currentImage = (fullImagePath, serverImagePath)
            responseMessage = ('{{"responseToCommand":"{}", "action":"{}", "fullImagePath":"{}", "serverImagePath":"{}"}}'
                               .format(command, action, fullImagePath, serverImagePath))
            self.write_message(responseMessage)

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
        global runScriptWebSocketConnections
        runScriptWebSocketConnections.add(self)

    def on_message(self, message):
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
    # If no pipe or no data to receive from pipe, we're done
    # Poll() is non-blocking whereas recv is blocking
    if (not runScriptWebSocketConnections
        or not scriptPipeConnection
        or not scriptPipeConnection.poll()):
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

# Returns a html page with a random image from outputDir
# Deprecated; use RandomImageBrowser instead
class GetRandomImageHandler(tornado.web.RequestHandler):
    def get(self):
        fullImagePath, serverImagePath = getRandomImage() 
        
        self.write('''<html><head><link rel="stylesheet" type="text/css" href="webInterface/styles.css"></head>
                            <body><p>{}</p><img class="maximize" src="{}"/></body>
                      </html>'''.format(fullImagePath, serverImagePath))

#
# Startup
#

def make_app():
    return tornado.web.Application([
        # Home page
        (r'/', HomeHandler),

        # Configure the script
        (r'/settings', SettingsHandler),

        # Handles messages for run script
        (r'/runScriptWebSocket', RunScriptWebSocket),

        # Handles messages for randomImageBrowser
        (r'/randomImageBrowserWebSocket', RandomImageBrowserWebSocket),

        # Static files
        (r'/webInterface/(.*)', tornado.web.StaticFileHandler, {'path' : 'webInterface'}),
        (r'/output/(.*)', tornado.web.StaticFileHandler, {'path' : settings.settings['Output_dir']}),
        
        # The old random image handler
        (r'/random', GetRandomImageHandler),
    ])

if __name__ == '__main__':
    print('\n\tWARNING: Do NOT run this server on the internet (e.g. port-forwarded)'
          ' nor when\n\t connected to an insecure LAN! It is not protected against malicious use.\n')
    
    print('Loading settings...')
    settings.getSettings()

    print('Liked Saved output directory: ' + settings.settings['Output_dir'])
    if not settings.settings['Output_dir']:
        print('WARNING: No output directory specified! This will probably break things')
    
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])
    
    port = 8888
    print('\nStarting LikedSavedDownloader Server on port {}...'.format(port))
    app = make_app()
    app.listen(port)
    ioLoop = tornado.ioloop.IOLoop.current()
    updateStatusCallback = tornado.ioloop.PeriodicCallback(updateScriptStatus, 100)
    updateStatusCallback.start()
    ioLoop.start()
