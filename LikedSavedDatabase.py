import os
import sqlite3
import submission as Submissions

# Global database
db = None

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

        cursor.execute("create table Submissions (id integer primary key, source text, title text, author text, subreddit text, subredditTitle text, body text, bodyUrl text, postUrl text, unique(postUrl))")
        cursor.execute("create table Comments (id integer primary key, source text, title text, author text, subreddit text, subredditTitle text, body text, bodyUrl text, postUrl text, unique(postUrl))")
        cursor.execute("create table Collections (id integer primary key, name text)")
        cursor.execute("create table SubmissionsToCollections (submissionKey integer, collectionKey integer, unique(submissionKey))")
        # Note that filePath is local to the server output directory,
        # not the root filesystem. Submission key doesn't have to be
        # unique so that multiple files can be associated with the
        # same submission (e.g. an album, or self-uploaded files)
        cursor.execute("create table FilesToSubmissions (filePath text, submissionKey integer, unique(filePath))")

        self.save()

    def save(self):
        self.dbConnection.commit()

    def addComment(self, submission):
        cursor = self.dbConnection.cursor()

        cursor.execute("insert or ignore into Comments values (NULL,?,?,?,?,?,?,?,?)",
                       submission.getAsList())
        self.save()

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

    def associateFileToSubmissionId(self, filePath, submissionId):
        cursor = self.dbConnection.cursor()
        cursor.execute("insert or ignore into FilesToSubmissions values (?,?)",
                       (filePath, submissionId))
        self.save()
        
    def associateFileToSubmission(self, filePath, submission):
        cursor = self.dbConnection.cursor()
        cursor.execute("select * from Submissions where postUrl=?", (submission.postUrl,))
        submissionInDb = cursor.fetchone()
        if submissionInDb:
            submissionId = submissionInDb[0]
            cursor.execute("insert or ignore into FilesToSubmissions values (?,?)",
                           (filePath, submissionId))
            self.save()
        else:
            print("DB error: couldn't find submission from post URL {}".format(submission.postUrl))

    def getAllSubmissionsInCollection(self, collectionId):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from Submissions, SubmissionsToCollections where Submissions.id = SubmissionsToCollections.submissionKey and SubmissionsToCollections.collectionKey = ?", (collectionId,))

        return cursor.fetchall()

    def getAllFiles(self):
        cursor = self.dbConnection.cursor()

        cursor.execute("select * from FilesToSubmissions")

        return cursor.fetchall()

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
    #testDatabase()
    testOnRealSubmissions()

