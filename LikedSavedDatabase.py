import os
import sqlite3
import submission as Submissions

class FavoritesCollection:
    def __init__(self, name):
        self.name = name
        self.collection = []

    def addFavorite(self, submission):
        self.collection.append(submission)

class LikedSavedDatabase:
    def __init__(self, databaseFilePath):
        isNewDatabase = not os.path.exists(databaseFilePath)
        self.dbConnection = sqlite3.connect(databaseFilePath)

        if isNewDatabase:
            self.initializeEmptyDatabase()

    def __del__(self):
        self.save()
        self.dbConnection.close()
        
    def initializeEmptyDatabase(self):
        cursor = self.dbConnection.cursor()
        
        cursor.execute("create table Submissions (id integer primary key, source text, title text, author text, subreddit text, subredditTitle text, body text, bodyUrl text, postUrl text)")
        cursor.execute("create table Collections (id integer primary key, name text)")
        cursor.execute("create table SubmissionsToCollections (submissionKey integer, collectionKey integer)")
        
        self.save()
        
    def save(self):
        self.dbConnection.commit()

    def addSubmission(self, submission):
        cursor = self.dbConnection.cursor()

        cursor.execute("insert into Submissions values (NULL,?,?,?,?,?,?,?,?)",
                       submission.getAsList())
        self.save()

    def printSubmissions(self):
        cursor = self.dbConnection.cursor()

        print("bunch of stuff: collections")
        for row in cursor.execute("select * from Submissions"):
            print(row)
        print("done")
    
    def getSubmissionByTitle(self, submissionTitle):
        cursor = self.dbConnection.cursor()

        # cursor.execute("select * from favorites where name=?", (collectionName,))
        cursor.execute("select * from Submissions where title=?", (submissionTitle,))
        return cursor.fetchone()
    
    def createCollection(self, collectionName):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert into Collections values (NULL, ?)", (collectionName,))
        self.save()

        # print("bunch of stuff: collections")
        # for row in cursor.execute("select * from Collections"):
            # print(row)
        # print("done")
        
        cursor.execute("select * from Collections where name=?", (collectionName,))
        return cursor.fetchone()

    def addSubmissionToCollection(self, submissionId, collectionId):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert into SubmissionsToCollections values (?,?)",
                       (submissionId, collectionId))
        self.save()

    def getAllSubmissionsInCollection(self, collectionId):
        cursor = self.dbConnection.cursor()
        
        cursor.execute("select * from Submissions, SubmissionsToCollections where Submissions.id = SubmissionsToCollections.submissionKey and SubmissionsToCollections.collectionKey = ?", (collectionId,))

        return cursor.fetchone()

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
    dbSubmission = db.getSubmissionByTitle("title")
    dbCollection = db.createCollection("myCollection")
    print(dbSubmission)
    print(dbCollection)
    db.addSubmissionToCollection(dbSubmission[0], dbCollection[0])
    print(db.getAllSubmissionsInCollection(dbCollection[0]))

def testOnRealSubmissions():
    submissions = Submissions.readCacheSubmissions("Reddit_SubmissionCache.bin")
    db = LikedSavedDatabase('test.db')
    for submission in submissions:
        db.addSubmission(submission)
    db.printSubmissions()

if __name__ == '__main__':
    #testDatabase()
    testOnRealSubmissions()

