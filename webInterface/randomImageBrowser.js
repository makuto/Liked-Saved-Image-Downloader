var ws = new WebSocket("ws://" + window.location.host + "/randomImageBrowserWebSocket");
var username = "likedSavedBrowserClient";

function sendMessage(message) {
    var payload = {
        "command": message,
        "user": username
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}

ws.onmessage = function(evt) {
    var messageDict = JSON.parse(evt.data);

    document.getElementById("message").innerHTML = messageDict.serverImagePath + " (" + messageDict.responseToCommand + ")";

	var videoContainer = document.getElementById("videoContainer");
	
    if (messageDict.action == "setImage") {
		// Clear any video
		videoContainer.innerHTML = null;
		
        document.body.style.backgroundImage = "url('/" + messageDict.serverImagePath + "')";
    }
	
	if (messageDict.action == "setVideo") {
		// Clear the image
		document.body.style.backgroundImage = null;

		// This would work except for the fact that the web server doesn't handle streaming video yet
		/*videoContainer.innerHTML = '<video class="video" width="500" height="500" autoplay loop="loop" controls><source src="'
			+ messageDict.serverImagePath
			+ '" type="video/mp4">Your browser does not support the video tag</video>';*/
		videoContainer.innerHTML = '<a class="bigCenterLink" target="_blank" href="http://'
			+ window.location.host + '/' + messageDict.serverImagePath
			+ '">View Video</a>';
	}
};

document.addEventListener("DOMContentLoaded", function() {
    // This is a stupid hack because I couldn't figure out when the web socket actually connects (I'm so lazy)
    setTimeout(function() {
        sendMessage("nextImage");
    }, 200);
}, false);

function onOpacityChanged(newValue) {
    var elements = document.getElementsByClassName("affectOpacity");
    var newOpacity = parseFloat(newValue);
    console.log(newOpacity);
    if (newOpacity == 0.0) {
        newOpacity = 0.05;
    }

    for (var i = 0; i < elements.length; i++) {
        elements[i].style.opacity = newOpacity;
    }
}

// From https://stackoverflow.com/questions/19440344/html5-fullscreen-browser-toggle-button
function toggleFullScreen() {
    if (!document.fullscreenElement && // alternative standard method
        !document.mozFullScreenElement && !document.webkitFullscreenElement) { // current working methods
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen();
        } else if (document.documentElement.mozRequestFullScreen) {
            document.documentElement.mozRequestFullScreen();
        } else if (document.documentElement.webkitRequestFullscreen) {
            document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
        }
    } else {
        if (document.cancelFullScreen) {
            document.cancelFullScreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitCancelFullScreen) {
            document.webkitCancelFullScreen();
        }
    }
}
