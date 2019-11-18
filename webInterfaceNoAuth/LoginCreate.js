
var passwordField = document.getElementById('password');
var verifyPasswordField = document.getElementById('verifyPassword');
var statusField = document.getElementById('passwordStatus');
var setPasswordSubmitButton = document.getElementById('setPasswordSubmit');

var verifyPasswords =
    function() {
	if (!passwordField.value)
	{
		/* statusField.style.display = 'block'; */
		statusField.innerText = 'Password must not be empty';
		setPasswordSubmitButton.disabled = true;
	}
	else if (verifyPasswordField.value != passwordField.value)
	{
		/* statusField.style.display = 'block'; */
		statusField.innerText = 'Passwords do not match';
		setPasswordSubmitButton.disabled = true;
	}
	else
	{
		/* statusField.style.display = 'none'; */
		statusField.innerText = '';
		setPasswordSubmitButton.disabled = false;
	}
}

verifyPasswordField.onkeyup = verifyPasswords;
passwordField.onkeyup = verifyPasswords;
