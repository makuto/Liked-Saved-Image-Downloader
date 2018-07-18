#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.websocket

import os
import random
import shutil
import json

outputDir = '/media/macoy/Shared/Backups/Web/Reddit/output'

savedImagesCache = []
def generateSavedImagesCache(outputDir):
    for root, dirs, files in os.walk(outputDir):
        for file in files:
            if file.endswith(('.gif', '.jpg', '.jpeg', '.png')):
                savedImagesCache.append(os.path.join(root, file))

def getRandomImage():
    if not savedImagesCache:
        generateSavedImagesCache(outputDir)
            
    randomImage = random.choice(savedImagesCache)

    print('\tgetRandomImage(): Chose random image {}'.format(randomImage))

    # Dear gods, forgive me, this is weird; trim the full output path
    serverPath = 'output' + randomImage.split(outputDir)[1]

    return randomImage, serverPath

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('webInterface/index.html')

# Returns a html page with a random image from outputDir
class GetRandomImageHandler(tornado.web.RequestHandler):
    def get(self):
        randomImagePath, serverImagePath = getRandomImage() 
        
        self.write('''<html><head><link rel="stylesheet" type="text/css" href="webInterface/styles.css"></head>
                            <body><p>{}</p><img class="maximize" src="{}"/></body>
                      </html>'''.format(randomImagePath, serverImagePath))

class RandomImageBrowserWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    def open(self):
        self.connections.add(self)
        self.randomHistory = []
        self.randomHistoryIndex = -1
        self.favorites = []
        self.favoritesIndex = 0

    def on_message(self, message):
        print('RandomImageBrowserWebSocket: Received message ', message)
        parsedMessage = json.loads(message)
        command = parsedMessage['command']
        print('RandomImageBrowserWebSocket: Command ', command)
        action = ''

        if command == 'imageAddToFavorites':
            if (self.randomHistoryIndex >= 0
                and self.randomHistoryIndex < len(self.randomHistory)
                and self.randomHistory[self.randomHistoryIndex] not in self.favorites):
                self.favorites.append(self.randomHistory[self.randomHistoryIndex])
                self.favoritesIndex = len(self.favorites) - 1

        if command == 'nextFavorite':
            self.favoritesIndex += 1
            if self.favoritesIndex >= 0 and self.favoritesIndex < len(self.favorites):
                action = 'setImage'
                randomImagePath, serverImagePath = self.favorites[self.favoritesIndex]
            else:
                self.favoritesIndex = len(self.favorites) - 1
                if len(self.favorites):
                    action = 'setImage'
                    randomImagePath, serverImagePath = self.favorites[self.favoritesIndex]

        if command == 'previousFavorite' and len(self.favorites):
            action = 'setImage'

            if self.favoritesIndex > 0:
                self.favoritesIndex -= 1
                
            randomImagePath, serverImagePath = self.favorites[self.favoritesIndex]

        if command == 'nextImage':
            action = 'setImage'

            if self.randomHistoryIndex == -1 or self.randomHistoryIndex >= len(self.randomHistory) - 1:
                randomImagePath, serverImagePath = getRandomImage()
                self.randomHistory.append((randomImagePath, serverImagePath))
                self.randomHistoryIndex = len(self.randomHistory) - 1
            else:
                self.randomHistoryIndex += 1
                randomImagePath, serverImagePath = self.randomHistory[self.randomHistoryIndex]

        if command == 'previousImage':
            action = 'setImage'

            if self.randomHistoryIndex > 0:
                self.randomHistoryIndex -= 1
                
            randomImagePath, serverImagePath = self.randomHistory[self.randomHistoryIndex]

        if action:
            responseMessage = ('{{"responseToCommand":"{}", "action":"{}", "randomImagePath":"{}", "serverImagePath":"{}"}}'
                               .format(command, action, randomImagePath, serverImagePath))
            self.write_message(responseMessage)

    def on_close(self):
        self.connections.remove(self)

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
