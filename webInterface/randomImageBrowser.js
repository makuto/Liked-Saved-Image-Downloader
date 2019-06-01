var ws = new WebSocket("wss://" + window.location.host + "/randomImageBrowserWebSocket");
var username = "likedSavedBrowserClient";

var currentOpacity = 0.3;

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

    currentOpacity = newOpacity;
}

function sendMessage(message) {
    var payload = {
        "command": message,
        "user": username
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}

function toggleDisplayed(elementId) {
    var element = document.getElementById(elementId);
    if (element.style.display === "none") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}

function toggleDirectoryControls() {
    toggleDisplayed("directoryControls");
    toggleDisplayed("imageBrowserControls");
}

function directoryOrFileOnClick(path, serverPath, type) {
    return function() {
        console.log("Directory or file '" + path + "' clicked (" + type + ") server path: " + serverPath);

        if (type == "dir") {
            var payload = {
                "command": "changeDirectory",
                "path": path
            };

            // Clear filter (the user probably only wanted to filter at this level)
            document.getElementById("directoryFilter").value = "";
            ws.send(JSON.stringify(payload));
        }

        if (type == "video") {
            window.open("https://" + window.location.host + "/" + serverPath);
        }

        if (type == "image") {
            document.body.style.backgroundImage = "url('/" + serverPath + "')";
        }

        if (type == "file") {
            window.open("https://" + window.location.host + "/" + serverPath);
        }
    }
}

function directoryUpOnClick() {
    var payload = {
        "command": "directoryUp"
    };
    // Clear filter (the user probably only wanted to filter at this level
    document.getElementById("directoryFilter").value = "";
    ws.send(JSON.stringify(payload));
}

function directoryRootOnClick() {
    var payload = {
        "command": "directoryRoot"
    };
    // Clear filter (the user probably only wanted to filter at this level
    document.getElementById("directoryFilter").value = "";
    ws.send(JSON.stringify(payload));
}

ws.onmessage = function(evt) {
    var messageDict = JSON.parse(evt.data);

    var videoContainer = document.getElementById("videoContainer");

    if (messageDict.action == "setImage") {
        document.getElementById("message").innerHTML = messageDict.serverImagePath + " (" + messageDict.responseToCommand + ")";

        // Clear any video
        videoContainer.innerHTML = null;

        document.body.style.backgroundImage = "url('/" + messageDict.serverImagePath + "')";
    }

    if (messageDict.action == "setVideo") {
        document.getElementById("message").innerHTML = messageDict.serverImagePath + " (" + messageDict.responseToCommand + ")";

        // Clear the image
        document.body.style.backgroundImage = null;

        // This would work except for the fact that the web server doesn't handle streaming video yet
        /*videoContainer.innerHTML = '<video class="video" width="500" height="500" autoplay loop="loop" controls><source src="'
            + messageDict.serverImagePath
            + '" type="video/mp4">Your browser does not support the video tag</video>';*/
        videoContainer.innerHTML = '<a class="bigCenterLink" target="_blank" href="https://' +
            window.location.host + '/' + messageDict.serverImagePath +
            '">View Video ' + messageDict.serverImagePath + '</a>';
    }

    if (messageDict.action == "sendDirectory") {
        var directoryListOut = document.getElementById("directoryListContainer");

        // Clear previous list
        while (directoryListOut.firstChild) {
            directoryListOut.removeChild(directoryListOut.firstChild);
        }

        for (var i = 0; i < messageDict.directoryList.length; i++) {
            // Not sure where the leading space is coming from here
            var path = messageDict.directoryList[i].path;

            var newButton = document.createElement("button");
            newButton.classList.add("directoryOrFileButton");
            newButton.classList.add("affectOpacity");
            newButton.classList.add("directoryButton_" + messageDict.directoryList[i].type);
            newButton.onclick = directoryOrFileOnClick(path, messageDict.directoryList[i].serverPath,
                messageDict.directoryList[i].type);
            newButton.innerHTML = path;
            newButton.style.opacity = currentOpacity;

            directoryListOut.appendChild(newButton);
        }
    }
};

// As soon as the websocket opens, request the initial image
ws.onopen = function(event) {
    var serverStatus = document.getElementById("serverStatus");
    // Hide it if the socket is open, so it doesn't get in the way
    serverStatus.innerHTML = "";
    sendMessage("nextImage");
    sendMessage("listCurrentDirectory")
}

// As soon as the websocket opens, request the initial image
ws.onclose = function(event) {
    var serverStatus = document.getElementById("serverStatus");
    // Hide it if the socket is open, so it doesn't get in the way
    serverStatus.innerHTML = "Connection to server lost";
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        // Workaround for mobile not using CSS starting opacity
        onOpacityChanged('0.3');
    }, 100);
}, false);

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

function filterChanged(newValue) {
    var payload = {
        "command": "setFilter",
        "user": username,
        "filter": newValue
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}

function directoryFilterChanged(newValue) {
    var payload = {
        "command": "setDirectoryFilter",
        "user": username,
        "filter": newValue
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}
