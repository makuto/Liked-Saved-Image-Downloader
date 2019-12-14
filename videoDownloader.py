import re
import settings
import ssl
import youtube_dl

alreadyDownloadedSentinel = "Already Downloaded"

# See https://ytdl-org.github.io/youtube-dl/supportedsites.html
# This list is a subset because I don't know the link formats of all supported sites
youtubeDlSitesSupported = [
    "gfycat.com",
    "instagram.com", # Should get a proper integration of this eventually...
    "pornhub.com",
    "redtube.com",
    "spankbang.com",
    "streamable.com",
    "v.redd.it",
    "vid.me",
    "vimeo.com",
    "xnxx.com",
    "xvideos.com",
    "xhamster.com",
    "youtube.com",
    "youtu.be",
]

youtubeDlBlacklistSites = [
    # Use the gfycat api for these, if available (see conditional in shouldUseYoutubeDl)
    # "gfycat"
]

youtubeDL_filenameFormat = "%(title)s-%(id)s.%(ext)s"

class YoutubeDlLogger(object):
    def __init__(self):
        self.outputList = []

    def defaultOut(self, msg):
        outputString = "[YoutubeDL] {}".format(msg)
        self.outputList.append(outputString)
        print(outputString)
        
    def debug(self, msg):
        self.defaultOut(msg)

    def warning(self, msg):
        self.defaultOut(msg)

    def error(self, msg):
        self.defaultOut(msg)

def shouldUseYoutubeDl(url):
    for siteMask in youtubeDlSitesSupported:
        if siteMask in url:
            isBlacklisted = False
            for blacklistSite in youtubeDlBlacklistSites:
                if blacklistSite in url:
                    isBlacklisted = True
                    break

            # Use the gfycat api for these, if available
            if settings.settings['Gfycat_Client_id'] and 'gfycat.com' in url:
                print("Gfycat {} means {} url not downloading".format(settings.settings['Gfycat_Client_id'], url))
                isBlacklisted = True

            if isBlacklisted:
                # We probably have another downloader
                return False

            # YoutubeDL should support this site
            return True

    return False

# Returns (success or failure, output file or failure message)
def downloadVideo(outputPath, url):
    if not settings.settings['Should_download_videos']:
        return (False,
                "Option 'Should download videos' is disabled. Enable it in Settings to download this video.")
    if (not settings.settings['Should_download_youtube_videos']
        and ('youtu.be' in url or 'youtube.com' in url)):
        return (False,
                "Option 'Should download youtube videos' is disabled. Enable it in Settings to download this video.")

    # Used to parse output (unfortunately...)
    youtubeDlLogger = YoutubeDlLogger()
        
    youtubeDL_options = {"outtmpl": "{}/{}".format(outputPath, youtubeDL_filenameFormat),
                         "writethumbnail": True,
                         "writeinfojson": True,
                         "logger": youtubeDlLogger}
    youtubeDownloader = youtube_dl.YoutubeDL(youtubeDL_options)

    try:
        youtubeDownloader.download([url])
    except youtube_dl.utils.DownloadError as downloadError:
        print(downloadError)
        return (False, downloadError.__str__())
    except ssl.CertificateError as certError:
        print(certError)
        return (False, certError.__str__() + ". This is likely the website maintainer's fault.")

    # Successful download; let's figure out what the file is
    outputFilename = ""
    for line in youtubeDlLogger.outputList:
        destinationMatch = re.search(r'.* Destination: (.*)', line)
        if destinationMatch:
            outputFilename = destinationMatch[1]
            # Keep looking, in case there is a merge formats
            # break

        mergingMatch = re.search(r'Merging formats into "(.*)"', line)
        if mergingMatch:
            outputFilename = mergingMatch[1]

        # Bit of a weird case here
        alreadyDownloadedMatch = re.search(r'.* (.*) has already been downloaded', line)
        if alreadyDownloadedMatch:
            return (False, alreadyDownloadedSentinel)
            
    return (True, outputFilename)

# Test Video downloader    
if __name__ == '__main__':
    settings.getSettings()
    outputDirOverride = "LOCAL_testOutput"

    # Pairs of URL, expected result
    testUrls = [
        # ("my test URL", True)
    ]
    for urlTestPair in testUrls:
        url = urlTestPair[0]
        expectedSupport = urlTestPair[1]
        canDownload = shouldUseYoutubeDl(url)
        if expectedSupport != canDownload:
            print("URL {} expected shouldUseYoutubeDl to return {} but got {}"
                  .format(url, expectedSupport, canDownload))
            continue

        if not canDownload:
            print("Skipping URL {} (not supported, or shouldn't use YoutubeDL)".format(url))
            continue
        
        print("Downloading {}".format(url))
        result = downloadVideo(outputDirOverride, url)
        print(result)
