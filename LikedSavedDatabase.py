import json
import os
import re
import sqlite3

# local imports
import settings
import submission as Submissions

# Global database
db = None

class LikedSavedDatabase:
    def __init__(self, databaseFilePath):
        print("Intializing database at {}".format(databaseFilePath))

        self.dbConnection = sqlite3.connect(databaseFilePath)

        # This gives us the ability to access results by column name
        # See https://docs.python.org/3/library/sqlite3.html#row-objects
        self.dbConnection.row_factory = sqlite3.Row

        self.initializeDatabaseTables()

    def __del__(self):
        self.save()
        self.dbConnection.close()

    def initializeDatabaseTables(self):
        cursor = self.dbConnection.cursor()

        cursor.execute("create table if not exists Submissions"
                       "(id integer primary key, source text, title text, author text, subreddit text, subredditTitle text, body text, bodyUrl text, postUrl text, unique(postUrl))")
        cursor.execute("create table if not exists Comments"
                       " (id integer primary key, source text, title text, author text, subreddit text, subredditTitle text, body text, bodyUrl text, postUrl text, unique(postUrl))")
        
        cursor.execute("create table if not exists Collections"
                       "(id integer primary key, name text)")
        # TODO: Does it not make sense to have unique files and
        # submissions because it should be possible for the same file
        # to be in multiple collections?
        cursor.execute("create table if not exists SubmissionsToCollections"
                       " (submissionKey integer, collectionKey integer, unique(submissionKey))")
        # For files in the output directory but not related to a submission (in case the user manually
        #put files they wanted to browse with the web interface
        cursor.execute("create table if not exists FilesToCollections"
                       "(filePath text, collectionKey integer, unique(filePath))")

        # Note that filePath is local to the server output directory,
        # not the root filesystem. Submission key doesn't have to be
        # unique so that multiple files can be associated with the
        # same submission (e.g. an album, or self-uploaded files)
        cursor.execute("create table if not exists FilesToSubmissions"
                       " (filePath text, submissionKey integer, unique(filePath))")

        cursor.execute("create table if not exists UnsupportedSubmissions"
                       "(submissionKey integer, reasonForFailure text, unique(submissionKey))")

        self.save()

    def save(self):
        self.dbConnection.commit()

    def addComment(self, submission):
        cursor = self.dbConnection.cursor()

        cursor.execute("insert or ignore into Comments values (NULL,?,?,?,?,?,?,?,?)",
                       submission.getAsList())
        self.save()
        
    def findSubmissionInDb(self, submission):
        cursor = self.dbConnection.cursor()
        
        # Find submission
        cursor.execute("select * from Submissions where postUrl=?", (submission.postUrl,))
        return cursor.fetchone()

    def findOrAddSubmission(self, submission):
        # Find submission
        submissionInDb = self.findSubmissionInDb(submission)
        # Submission not found
        if not submissionInDb:
            print("Submission not found; database out of sync? Adding it")
            self.addSubmission(submission)

        submissionInDb = self.findSubmissionInDb(submission)
        if not submissionInDb:
            print("Could not find submission after add. Something's wrong")
            return None

        return submissionInDb

    def addSubmission(self, submission):
        cursor = self.dbConnection.cursor()

        cursor.execute("insert or ignore into Submissions values (NULL,?,?,?,?,?,?,?,?)",
                       submission.getAsList())
        self.save()

    def addSubmissions(self, submissions):
        cursor = self.dbConnection.cursor()

        cursor.executemany("insert or ignore into Submissions values (NULL,?,?,?,?,?,?,?,?)",
                       Submissions.getAsList_generator(submissions))
        self.save()

    def printSubmissions(self):
        cursor = self.dbConnection.cursor()

        print("Submissions:")
        for row in cursor.execute("select * from Submissions"):
            print('\t', row)
        print("done")

    def getSubmissionsByTitle(self, submissionTitle):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from Submissions where title=?", (submissionTitle,))
        return cursor.fetchone()

    def createCollection(self, collectionName):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert into Collections values (NULL, ?)", (collectionName,))
        self.save()
        cursor.execute("select * from Collections where name=?", (collectionName,))
        return cursor.fetchone()

    def addSubmissionToCollection(self, submissionId, collectionId):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert or ignore into SubmissionsToCollections values (?,?)",
                       (submissionId, collectionId))
        self.save()

    # Collection by name or ID, whichever's more convenient
    def addFileToCollection(self, filePath, collection):
        cursor = self.dbConnection.cursor()
        collectionId = collection
        if type(collection) == str:
            cursor.execute("select * from Collections where name=?", (collection,))
            collectionId = cursor.fetchone()
            if not collectionId:
                print("Lazy-creating collection {}".format(collection))
                collectionId = self.createCollection(collection)[0]
            else:
                collectionId = collectionId[0]
    
        if not collectionId:
            print("Collection not found")
        else:
            print("{} into collection ID {}".format(filePath, collectionId))
            cursor.execute("insert or ignore into FilesToCollections values (?,?)",
                           (filePath, collectionId))
        self.save()

    def associateFileToSubmissionById(self, filePath, submissionId):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert or ignore into FilesToSubmissions values (?,?)",
                       (filePath, submissionId))
        self.save()
        
    def associateFileToSubmission(self, filePath, submission):
        submissionInDb = self.findSubmissionInDb(submission)
        if submissionInDb:
            submissionId = submissionInDb[0]
            self.associateFileToSubmissionById(filePath, submissionId)
        else:
            print("DB error: couldn't find submission from post URL {}".format(submission.postUrl))

    def onSuccessfulSubmissionDownload(self, submission, downloadedFilePath):
        self.associateFileToSubmission(downloadedFilePath, submission)

        # Submission should now be supported
        self.removeFromUnsupportedSubmissions(submission)

    def getAllSubmissionsInCollection(self, collectionId):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from Submissions, SubmissionsToCollections where Submissions.id = SubmissionsToCollections.submissionKey and SubmissionsToCollections.collectionKey = ?", (collectionId,))

        return cursor.fetchall()
    
    def getAllFilesInCollection(self, collectionId):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from FilesToCollections "
                       "where FilesToCollections.collectionKey = ?", (collectionId,))

        return cursor.fetchall()

    def getAllFiles(self):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from FilesToSubmissions")

        return cursor.fetchall()

    # This doesn't allow a different reason for each submission
    # TODO: Need to get IDs first
    # def addUnsupportedSubmissions(self, submissions, reasonForFailure):
    #     cursor = self.dbConnection.cursor()

    #     # Ignore because we will assume this is legacy reimport, so it's likely bad reasons anyways
    #     cursor.executemany("insert or ignore into UnsupportedSubmissions values (?,?)",
    #                        (Submissions.getAsList_generator(submissions), reasonForFailure))
    #     self.save()

    # Very slow, use addUnsupportedSubmissions when possible
    def addUnsupportedSubmission(self, submission, reasonForFailure):
        cursor = self.dbConnection.cursor()
        
        # Find submission
        submissionInDb = self.findOrAddSubmission(submission)
        if not submissionInDb:
            return

        # Replace the older one with the newer failure reason, in case the system has updated
        cursor.execute("insert or replace into UnsupportedSubmissions values (?,?)",
                       (submissionInDb[0], reasonForFailure))
        self.save()

    def removeFromUnsupportedSubmissions(self, submission):
        cursor = self.dbConnection.cursor()
        
        # Find submission
        submissionInDb = self.findOrAddSubmission(submission)
        if not submissionInDb:
            return

        cursor.execute("delete from UnsupportedSubmissions where submissionKey = ?",
                       (submissionInDb[0],))
        self.save()

    def removeUnsupportedSubmissionsWithFileAssociations(self):
        cursor = self.dbConnection.cursor()
        
        cursor.execute("delete from UnsupportedSubmissions "
                       "where UnsupportedSubmissions.submissionKey in (select submissionKey from FilesToSubmissions)")
        self.save()

    def getAllUnsupportedSubmissions(self):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from Submissions, UnsupportedSubmissions "
                       "where Submissions.id = UnsupportedSubmissions.submissionKey")

        return cursor.fetchall()

    def getSubmissionsByIds(self, submissionIds):
        if not submissionIds:
            return []
        
        cursor = self.dbConnection.cursor()
        cursor.execute("drop table if exists RequestedSubmissions")
        cursor.execute("create temporary table RequestedSubmissions (id integer, unique(id))")

        submissionTuples = [(i,) for i in submissionIds]
        cursor.executemany("insert or ignore into RequestedSubmissions values (?)", submissionTuples)
        
        cursor.execute("select * from Submissions, RequestedSubmissions "
                       "where Submissions.id = RequestedSubmissions.id")
        return cursor.fetchall()

    def getMissingPixivSubmissionIds(self):
        cursor = self.dbConnection.cursor()
        cursor.execute('select Submissions.id from Submissions where Submissions.source = "Pixiv"'
                       'and Submissions.id not in (select submissionKey from FilesToSubmissions)')
        return cursor.fetchall()


def initializeFromSettings(userSettings):
    global db
    if not db:
        db = LikedSavedDatabase(userSettings['Database'])
'''
Importing
'''

def submissionsFromJsonFiles(jsonFilesToRead):
    submissions = []
    for filename in jsonFilesToRead:
        file = open(filename, 'r')
        # Ugh...
        lines = file.readlines()
        text = u''.join(lines)
        # Fix the formatting so the json module understands it
        text = "[{}]".format(text[1:-3])
        
        dictSubmissions = json.loads(text)
        for dictSubmission in dictSubmissions:
            submission = Submissions.Submission()
            submission.initFromDict(dictSubmission)
            submissions.append(submission)
        print("Read {} submissions from file {}".format(len(dictSubmissions), filename))
            
    totalSubmissions = len(submissions)
    return (submissions, totalSubmissions)

# This should only need to be executed if you ran the script before db support was added
def importFromAllJsonInDir(dir):
    global db

    jsonFilesToRead = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            match = re.search(r'AllSubmissions_(.*).json', file)
            if match:
                jsonFilesToRead.append(os.path.join(root, file))

    print("Importing {} AllSubmissions json files in {}...".format(len(jsonFilesToRead), dir))

    submissions, totalSubmissions = submissionsFromJsonFiles(jsonFilesToRead)

    print("Adding {} submissions to database...".format(totalSubmissions))
    db.addSubmissions(submissions)
    print("Successfully added {} submissions".format(totalSubmissions))

def importUnsupportedSubmissionsFromAllJsonInDir(dir):
    global db

    jsonFilesToRead = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            match = re.search(r'UnsupportedSubmissions_(.*).json', file)
            if match:
                jsonFilesToRead.append(os.path.join(root, file))
                
    print("Importing {} UnsupportedSubmissions json files...".format(len(jsonFilesToRead)))

    submissions, totalSubmissions = submissionsFromJsonFiles(jsonFilesToRead)

    print("Adding {} submissions to database...".format(totalSubmissions))
    for submission in submissions:
        db.addUnsupportedSubmission(submission, "Reason unknown (legacy)")
    print("Successfully added {} submissions".format(totalSubmissions))


'''
Testing
'''

def testDatabase():
    db = LikedSavedDatabase('test.db')
    testSubmission = Submissions.Submission()
    testSubmission.source = "source"
    testSubmission.title = "title"
    testSubmission.author = "author"
    testSubmission.subreddit = "subreddit"
    testSubmission.subredditTitle = "subredditTitle"
    testSubmission.body = "body"
    testSubmission.bodyUrl = "bodyUrl"
    testSubmission.postUrl = "postUrl"
    db.addSubmission(testSubmission)
    dbSubmission = db.getSubmissionsByTitle("title")
    dbCollection = db.createCollection("myCollection")
    print(dbSubmission[0])
    print(dbCollection)
    db.addSubmissionToCollection(dbSubmission[0], dbCollection[0])
    print(db.getAllSubmissionsInCollection(dbCollection[0]))

def testOnRealSubmissions():
    submissions = Submissions.readCacheSubmissions("Reddit_SubmissionCache.bin")
    db = LikedSavedDatabase('test_v6.db')
    for submission in submissions:
        db.addSubmission(submission)
    db.printSubmissions()
    dbCollection = db.createCollection("myCollection")

    for title in ["Test 1", "Test 2"]:
        dbSubmission = db.getSubmissionsByTitle(title)
        if not dbSubmission:
            print("Couldn't find {}".format(title))
        else:
            db.addSubmissionToCollection(dbSubmission[0], dbCollection[0])
            db.associateFileToSubmissionId("{}.png".format(title), dbSubmission[0])

    print(db.getAllSubmissionsInCollection(dbCollection[0]))
    print(db.getAllFiles())
    
def initializeFromSettings(userSettings):
    global db
    db = LikedSavedDatabase(userSettings['Database'])

if __name__ == '__main__':
    # Old, may not work
    #testDatabase()
    
    # testOnRealSubmissions()
    
    settings.getSettings()
    # initializeFromSettings(settings.settings)
    db = LikedSavedDatabase("TestImport.db")
    importFromAllJsonInDir(settings.settings["Metadata_output_dir"])
