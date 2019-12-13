import youtube_dl

youtubedlSitesSupported = [
    "youtu.be",
    "youtube.com",
    "v.redd.it",
    "pornhub.com",
    "xvideos.com"
]

youtubeelBlacklistSites = [
    # Use the gfycat api for these
    "gfycat"
]

youtubeDL_filenameFormat = "%(title)s-%(id)s.%(ext)s"

# TODO: Should almost certainly do thumbnail saving, and might as well save video info!

youtubeDL_options = None
youtubeDownloader = None

def shouldUseYoutubeDl(url):
    for siteMask in youtubedlSitesSupported:
        if siteMask in url:
            isBlacklisted = False
            for blacklistSite in youtubeelBlacklistSites:
                if blacklistSite in url:
                    isBlacklisted = True
                    break

            if isBlacklisted:
                # We probably have another downloader
                return False

            # YoutubeDL should support this site
            return True

    return False

def downloadVideo(url):
    global youtubeDownloader
    if not youtubeDownloader:
        # Lazy initialize downloader
        youtubeDownloader = youtube_dl.YoutubeDL(youtubeDL_options if youtubeDL_options else {})

    try:
        youtubeDownloader.download([url])
    except youtube_dl.utils.DownloadError as downloadError:
        print(downloadError)
        return (False, downloadError.__str__())

    return (True, "")

# Test Video downloader    
if __name__ == '__main__':
    outputDir = "LOCAL_testOutput"
    youtubeDL_options = {"outtmpl":"{}/{}".format(outputDir, youtubeDL_filenameFormat)}

    # Pairs of URL, expected result
    testUrls = [
        # ("myurl", False)
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
        downloadVideo(url)
