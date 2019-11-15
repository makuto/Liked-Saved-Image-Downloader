import os

import logger
import redditScraper
import tumblrScraper
import submission
import settings
import LikedSavedDatabase

# Unfortunately, this can only ever get 1000 (reddit's imposed limit)
def AddAllFromReddit(database, settings):
    if not settings.hasRedditSettings():
        logger.log('Reddit settings are not provided!')
        return

    submissions = []

    logger.log('Adding last 1000 liked/saved submissions from Reddit. This will take a long time.')

    redditSubmissions, redditComments, earlyOutPoints = redditScraper.getRedditUserLikedSavedSubmissions(
        settings.settings['Username'], settings.settings['Password'], 
        settings.settings['Client_id'], settings.settings['Client_secret'],
        request_limit = None, # No limit = request as many as possible (1000)
        saveLiked = settings.settings['Reddit_Save_Liked'], 
        saveSaved = settings.settings['Reddit_Save_Saved'],
        earlyOutPointSaved = None, 
        earlyOutPointLiked = None,
        unlikeLiked = False,
        unsaveSaved = False)

    logger.log('Retrieved submissions, adding to database...')

    for submission in redditSubmissions:
        database.addSubmission(submission)

    for comment in redditComments:
        database.addComment(comment)

    logger.log('Done! Saved {} submissions and {} comments'.format(len(redditSubmissions), len(redditComments)))
    
def AddAllFromDirectory(fileDatabase, directory):
    logger.log('Scanning {} to create FileCollectionDatabase'.format(directory))
    numFiles = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            fileDatabase.addFileNoSave(file, os.path.relpath(os.path.join(root, file), directory))
            numFiles += 1
            
    fileDatabase.save()

    logger.log('Done; {} files in database'.format(numFiles))

if __name__ == '__main__':
    createSubmissionsDatabase = False
    createFileCollectionDatabase = True
    if createSubmissionsDatabase:
        databaseFilename = 'LikedSavedDatabase.db'
        isNewDatabase = not os.path.exists(databaseFilename)
        if isNewDatabase:
            db = LikedSavedDatabase.LikedSavedDatabase(databaseFilename)
            settings.getSettings()
            
            AddAllFromReddit(db, settings)
            
    if createFileCollectionDatabase:
        databaseFilename = 'FileCollectionDatabase.db'
        isNewDatabase = not os.path.exists(databaseFilename)
        if isNewDatabase:
            db = LikedSavedDatabase.FileCollectionDatabase(databaseFilename)
            settings.getSettings()
            
            AddAllFromDirectory(db, settings.settings['Output_dir'])
