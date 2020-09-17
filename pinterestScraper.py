from py3pin.Pinterest import Pinterest
from submission import Submission
import logger
import os
import pickle

def getPinterestUserPinnedSubmissions(email, username, password, cacheFileName):

    submissions = []

    lastIds = {} if not cacheFileName else loadPinterestCache(cacheFileName)
    updatedLastIds = lastIds

    pinterest = Pinterest(email=email,
                          password=password,
                          username=username,
                          cred_root='pinterest_creds')

    logger.log("Logging in to Pinterest...")
    pinterest.login()

    boards = pinterest.boards(username=username)

    for board in boards:
        # Get all pins for the board
        board_pins = []
        pin_batch = pinterest.board_feed(board_id=board['id'])

        while len(pin_batch) > 0:
            for pin in pin_batch:
                if pin['id'] not in lastIds:
                    # Only using the dict for its key lookup
                    updatedLastIds[pin['id']] = 1
                    board_pins.append(pin)

            pin_batch = pinterest.board_feed(board_id=board['id'])

        for pin in board_pins:

            # I'm not sure how important it is to support these
            if pin['type'] == 'story':
                continue

            newSubmission = Submission()
            newSubmission.source = u'Pinterest'
            # While pins do have titles, 90% of the time they seem useless
            newSubmission.title = pin['id']
            # There is probably a way to figure out who the original pinner is, but oh well
            newSubmission.author = 'N/A'
            newSubmission.subreddit = board['url']
            newSubmission.subredditTitle = board['name'] + '_Pinterest'
            if 'rich_summary' in pin and pin['rich_summary']:
                if 'display_description' in pin['rich_summary']:
                    newSubmission.body = pin['rich_summary']['display_description']
                else:
                    newSubmission.body = 'N/A'
                newSubmission.postUrl = pin['rich_summary']['url']

            # What is actually downloaded
            newSubmission.bodyUrl = pin['images']['orig']['url']
            submissions.append(newSubmission)

    if cacheFileName:
        savePinterestCache(cacheFileName, updatedLastIds)

    logger.log("Found {} new Pinterest submissions".format(len(submissions)))
    return submissions

def savePinterestCache(cacheFileName, mostRecentIdPerBoard):
    cacheFile = open(cacheFileName, 'wb')
    pickle.dump(mostRecentIdPerBoard, cacheFile)

def loadPinterestCache(cacheFileName):
    if os.path.exists(cacheFileName):
        cacheFile = open(cacheFileName, 'rb')
        mostRecentIdPerBoard = pickle.load(cacheFile)
        return mostRecentIdPerBoard
    else:
        return {}

if __name__ == '__main__':
    submissions = getPinterestUserPinnedSubmissions('my@email.com', 'myusername', 'password')
    for pinterestSubmission in submissions:
        print('{}\n\n'.format(pinterestSubmission.getXML()))

