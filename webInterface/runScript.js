var ws = new WebSocket((useSSL ? "wss://" : "ws://") + window.location.host + "/runScriptWebSocket");

var username = "likedSavedBrowserClient";

// As soon as the websocket opens, request the initial image
ws.onopen = function(event) {
    var serverStatus = document.getElementById("serverStatus");
    // Hide it if the socket is open, so it doesn't get in the way
    serverStatus.innerHTML = "";
}

// As soon as the websocket opens, request the initial image
ws.onclose = function(event) {
    var serverStatus = document.getElementById("serverStatus");
    // Hide it if the socket is open, so it doesn't get in the way
    serverStatus.innerHTML = "Connection to server lost. Reload the page to attempt to reconnect.";
}

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

    if (messageDict.action == "printMessage") {
        document.getElementById("messages").innerText += messageDict.message
    } else if (messageDict.action == "scriptFinished") {
        document.getElementById("runScriptButton").style.display = "block";
    }
};

function onRunScriptClicked() {
	document.getElementById("messages").innerText = "";
    sendMessage("runScript");
    document.getElementById("runScriptButton").style.display = "none";
}

function onExplicitDownloadClicked() {
	document.getElementById("messages").innerText = "";
    // document.getElementById("runScriptButton").style.display = "none";

    explicitDownloadText = document.getElementById("explicitDownloadUrls").value;
    var payload = {
        "command": "explicitDownloadUrls",
        "urls": explicitDownloadText
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}

function clearExplicitDownloadClicked() {
    urls = document.getElementById("explicitDownloadUrls")
    urls.value = '';
}

function onRefreshCacheClicked() {
	document.getElementById("messages").innerText = "";
    sendMessage("refreshCache");
}

function smartClearBox() {
    urls = document.getElementById("explicitDownloadUrls")
    if (urls.value =="Enter URLs here")
        urls.value = '';
}
