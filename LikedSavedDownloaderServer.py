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

from utilities import sort_naturally
import settings

videoExtensions = ('.mp4')
supportedExtensions = ('.gif', '.jpg', '.jpeg', '.png', '.mp4')

savedImagesCache = []
def generateSavedImagesCache(outputDir):
    for root, dirs, files in os.walk(outputDir):
        for file in files:
            if file.endswith(supportedExtensions):
                savedImagesCache.append(os.path.join(root, file))

def outputPathToServerPath(path):
    return 'output' + path.split(settings.settings['Output_dir'])[1]

def getRandomImage():
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])
            
    randomImage = random.choice(savedImagesCache)

    print('\tgetRandomImage(): Chose random image {}'.format(randomImage))

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

# Returns a html page with a random image from outputDir
class GetRandomImageHandler(tornado.web.RequestHandler):
    def get(self):
        fullImagePath, serverImagePath = getRandomImage() 
        
        self.write('''<html><head><link rel="stylesheet" type="text/css" href="webInterface/styles.css"></head>
                            <body><p>{}</p><img class="maximize" src="{}"/></body>
                      </html>'''.format(fullImagePath, serverImagePath))

class RandomImageBrowserWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    def open(self):
        self.connections.add(self)
        self.randomHistory = []
        self.randomHistoryIndex = -1
        self.favorites = []
        self.favoritesIndex = 0
        self.currentImage = None

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
                fullImagePath, serverImagePath = getRandomImage()
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

#
# Startup
#

def make_app():
    return tornado.web.Application([
        # Home page
        (r'/', HomeHandler),

        # Configure the script
        (r'/settings', SettingsHandler),

        # Handles messages for randomImageBrowser
        (r'/randomImageBrowserWebSocket', RandomImageBrowserWebSocket),

        # Static files
        (r'/webInterface/(.*)', tornado.web.StaticFileHandler, {'path' : 'webInterface'}),
        (r'/output/(.*)', tornado.web.StaticFileHandler, {'path' : settings.settings['Output_dir']}),
        
        # The old random image handler
        (r'/random', GetRandomImageHandler),
    ])

if __name__ == '__main__':
    print('Grabbing settings...')
    settings.getSettings()

    print('Output: ' + settings.settings['Output_dir'])
    
    print('Creating cache...')
    if not savedImagesCache:
        generateSavedImagesCache(settings.settings['Output_dir'])
    
    port = 8888
    print('Starting LikedSavedDownloader Tornado Server on port {}...'.format(port))
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
