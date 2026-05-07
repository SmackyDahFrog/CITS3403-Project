let usernameCheckTimer = null;
// last verdict from /check-username, kept here so updateSubmitState can read it
let usernameAvailable = false;

function validateUsername() {
    const input = document.getElementById('username');
    const error = document.getElementById('usernameError');
    const status = document.getElementById('usernameStatus');
    const value = input.value.trim();

    // hide any stale availability message while the user is still typing
    status.style.display = 'none';
    status.textContent = '';
    usernameAvailable = false;

    // server-side error from a previous submit no longer applies once user types
    clearServerError('username');

    if (value.length>0 && value.length<4){
        error.style.display = 'block';
        input.classList.add('input-invalid');
        input.classList.remove('input-valid');
        clearTimeout(usernameCheckTimer);
    }
    else if (value.length >= 4){
        error.style.display = 'none';
        // hold off on the styling until the server confirms availability
        input.classList.remove('input-valid', 'input-invalid');
        // show that we're about to check before the request lands
        status.style.display = 'block';
        status.className = 'small username-checking';
        status.textContent = 'Checking...';
        // debounce so we don't fire a request on every keystroke
        clearTimeout(usernameCheckTimer);
        usernameCheckTimer = setTimeout(function(){ checkUsernameAvailability(value); }, 300);
    }
    else{
        error.style.display = 'none';
        input.classList.remove('input-valid', 'input-invalid');
        clearTimeout(usernameCheckTimer);
    }
    updateSubmitState();
}

function checkUsernameAvailability(username){
    const input = document.getElementById('username');
    const status = document.getElementById('usernameStatus');

    fetch('/check-username?username=' + encodeURIComponent(username))
        .then(function(res){ return res.json(); })
        .then(function(data){
            // ignore stale responses if the user has kept typing past this value
            if (input.value.trim() !== username) return;

            status.style.display = 'block';
            if (data.available){
                status.className = 'text-success small';
                status.textContent = 'Username is available.';
                input.classList.add('input-valid');
                input.classList.remove('input-invalid');
                usernameAvailable = true;
            } else {
                status.className = 'text-danger small';
                if (data.reason === 'taken') {
                    status.textContent = 'That username is already taken.';
                } else if (data.reason === 'rate_limited') {
                    status.textContent = 'Slow down a moment, then try again.';
                } else if (data.reason === 'invalid') {
                    status.textContent = 'Letters, numbers, _ and - only.';
                } else {
                    status.textContent = 'Username is not valid.';
                }
                input.classList.add('input-invalid');
                input.classList.remove('input-valid');
                usernameAvailable = false;
            }
            updateSubmitState();
        })
        .catch(function(){
            // network hiccup, clear styling so the form stays usable
            status.style.display = 'none';
            input.classList.remove('input-valid', 'input-invalid');
            usernameAvailable = false;
            updateSubmitState();
        });
}

function passwordRulesAllMet(){
    const value = document.getElementById('password').value;
    return value.length >= 8
        && /[a-zA-Z]/.test(value)
        && /[0-9]/.test(value)
        && /[!@#$%&*_]/.test(value);
}

function validatePasswords(){
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');
    const error = document.getElementById('passwordError');
    const value = password.value;
    const confirmValue = confirmPassword.value;

    // typing into either password field invalidates the server-side warnings
    clearServerError('password');
    clearServerError('confirm_password');

    const hasLength = value.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    const hasSymbol = /[!@#$%&*_]/.test(value);

    if (value.length > 0 && (!hasLength || !hasLetter || !hasNumber || !hasSymbol)){
        password.classList.add('input-invalid');
        password.classList.remove('input-valid');
    }
    else if (value.length >= 8 && hasLetter && hasNumber && hasSymbol){
        password.classList.add('input-valid');
        password.classList.remove('input-invalid');

        if (confirmValue.length > 0 && confirmValue !== value) {
            error.style.display = 'block';
            error.textContent = 'Passwords do not match.';
            confirmPassword.classList.add('input-invalid');
            confirmPassword.classList.remove('input-valid');
        } else if (confirmValue === value) {
            error.style.display = 'none';
            confirmPassword.classList.add('input-valid');
            confirmPassword.classList.remove('input-invalid');
        }
    }
    else {
        error.style.display = 'none';
        password.classList.remove('input-valid', 'input-invalid');
        confirmPassword.classList.remove('input-valid', 'input-invalid');
    }

    updateSubmitState();
}

function clearServerError(fieldName) {
    const nodes = document.querySelectorAll('.server-error[data-field="' + fieldName + '"]');
    nodes.forEach(function(n){ n.style.display = 'none'; });
}

function updateSubmitState(){
    const button = document.getElementById('signupSubmit');
    if (!button) return;
    const username = document.getElementById('username').value.trim();
    const okUsername = username.length >= 4 && usernameAvailable;
    const okPassword = passwordRulesAllMet();
    const confirmValue = document.getElementById('confirmPassword').value;
    const okConfirm = confirmValue.length > 0 && confirmValue === document.getElementById('password').value;
    button.disabled = !(okUsername && okPassword && okConfirm);
}

document.addEventListener('DOMContentLoaded', function(){
    // run once so a server-rendered username value still gets checked and styled
    const usernameInput = document.getElementById('username');
    if (usernameInput && usernameInput.value.trim().length >= 4) {
        validateUsername();
    } else {
        updateSubmitState();
    }

    // when the server kicked us back with errors, drop focus on the first bad field
    const firstServerError = document.querySelector('.server-error');
    if (firstServerError) {
        const fieldName = firstServerError.getAttribute('data-field');
        const target = document.querySelector('[name="' + fieldName + '"]');
        if (target) target.focus();
    }
});
