var ws = new WebSocket("ws://" + window.location.host + "/runScriptWebSocket");
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
