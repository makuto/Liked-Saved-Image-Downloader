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

# TODO: Remove
outputDir = '/media/macoy/Shared/Backups/Web/Reddit/output'

videoExtensions = ('.mp4')
supportedExtensions = ('.gif', '.jpg', '.jpeg', '.png', '.mp4')

savedImagesCache = []
def generateSavedImagesCache(outputDir):
    for root, dirs, files in os.walk(outputDir):
        for file in files:
            if file.endswith(supportedExtensions):
                savedImagesCache.append(os.path.join(root, file))

def outputPathToServerPath(path):
    return 'output' + path.split(outputDir)[1]

def getRandomImage():
    if not savedImagesCache:
        generateSavedImagesCache(outputDir)
            
    randomImage = random.choice(savedImagesCache)

    print('\tgetRandomImage(): Chose random image {}'.format(randomImage))

    # Dear gods, forgive me, this is weird; trim the full output path
    serverPath = outputPathToServerPath(randomImage)

    return randomImage, serverPath

#
# Tornado handlers
#

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('webInterface/index.html')

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
        (r'/', MainHandler),
        (r'/randomImageBrowserWebSocket', RandomImageBrowserWebSocket),
        (r'/random', GetRandomImageHandler),
        (r'/webInterface/(.*)', tornado.web.StaticFileHandler, {'path':'webInterface'}),
        (r'/output/(.*)', tornado.web.StaticFileHandler, {'path':outputDir})
    ])

if __name__ == '__main__':
    print("Starting LikedSavedDownloader Tornado Server...")
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
