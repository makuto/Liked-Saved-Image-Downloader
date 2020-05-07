var ws = new WebSocket((useSSL ? "wss://" : "ws://") + window.location.host + "/runScriptWebSocket");

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

ws.onmessage = function(evt) {
    var messageDict = JSON.parse(evt.data);

    if (messageDict.action == "printMessage") {
        document.getElementById("messages").innerText += messageDict.message
	}
    //} else if (messageDict.action == "scriptFinished") {
        //document.getElementById("runScriptButton").style.display = "block";
    //}
};

var shouldToggleOn = true;
function toggleRetryAll()
{
	submissions = document.getElementsByName('shouldRetry');
	for (let i = 0; i < submissions.length; i++)
	{
		submissions[i].checked = shouldToggleOn;
	}

	shouldToggleOn = !shouldToggleOn;
}

function retrySelected()
{
	submissions = document.getElementsByName('shouldRetry');
	submissionsToRetry = []
	for (let i = 0; i < submissions.length; i++)
	{
		if (!submissions[i].checked)
			continue;

		// Collate checked into list of submissions to retry
		submissionsToRetry.push(parseInt(submissions[i].value));
	}

	var payload = {
        "command": "retrySubmissions",
        "submissionsToRetry": submissionsToRetry
    }

    // Make the request to the WebSocket.
    ws.send(JSON.stringify(payload));
}
