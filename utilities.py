# From https://stackoverflow.com/questions/4623446/how-do-you-sort-files-numerically
import re

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_naturally(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

def makeDirIfNonexistant(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
