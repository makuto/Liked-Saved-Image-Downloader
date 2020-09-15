from py3pin.Pinterest import Pinterest
from submission import Submission
import logger

def getPinterestUserPinnedSubmissions(email, username, password):
    pinterest = Pinterest(email=email,
                          password=password,
                          username=username,
                          cred_root='pinterest_creds')

    pinterest.login()

    submissions = []

    boards = pinterest.boards(username=username)

    for board in boards:
        # Get all pins for the board
        board_pins = []
        pin_batch = pinterest.board_feed(board_id=board['id'])
        while len(pin_batch) > 0:
            board_pins += pin_batch
            pin_batch = pinterest.board_feed(board_id=board['id'])

        for pin in board_pins:
            # url = pin['images']['orig']['url']
            # index = str(url).rfind('.')
            # extension = str(url)[index:]
            # download_image(url, download_dir + pin['id'] + extension)

            # I'm not sure how important it is to support these
            if pin['type'] == 'story':
                continue

            newSubmission = Submission()
            newSubmission.source = u'Pinterest'
            newSubmission.title = pin['grid_title'] if pin['grid_title'] else pin['id']
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

    return submissions

if __name__ == '__main__':
    submissions = getPinterestUserPinnedSubmissions('my@email.com', 'myusername', 'password')
    for pinterestSubmission in submissions:
        print('{}\n\n'.format(pinterestSubmission.getXML()))

