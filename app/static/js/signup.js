let usernameCheckTimer = null;
// only show the live availability + warnings once the user has actually touched the field
let usernameTouched = false;
let passwordTouched = false;
let confirmTouched = false;
// last verdict from /check-username, kept here so updateSubmitState can read it
let usernameAvailable = false;

function validateUsername() {
    const input = document.getElementById('username');
    const error = document.getElementById('usernameError');
    const status = document.getElementById('usernameStatus');
    const value = input.value.trim();
    usernameTouched = true;

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

function showPasswordRules(){
    const popup = document.getElementById('passwordRules');
    if (!popup) return;
    const value = document.getElementById('password').value;
    // the popup only appears once the user has actually started typing
    if (value.length > 0) {
        popup.style.display = 'block';
    }
}

function maybeHidePasswordRules(){
    const popup = document.getElementById('passwordRules');
    if (!popup) return;
    const value = document.getElementById('password').value;
    if (value.length === 0 || passwordRulesAllMet()) {
        popup.style.display = 'none';
    }
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
    const popup = document.getElementById('passwordRules');
    const value = password.value;
    const confirmValue = confirmPassword.value;

    if (document.activeElement === password && value.length > 0) {
        passwordTouched = true;
    }
    if (document.activeElement === confirmPassword && confirmValue.length > 0) {
        confirmTouched = true;
    }

    // typing into either password field invalidates the server-side warnings
    clearServerError('password');
    clearServerError('confirm_password');

    const checks = {
        length: value.length >= 8,
        letter: /[a-zA-Z]/.test(value),
        number: /[0-9]/.test(value),
        symbol: /[!@#$%&*_]/.test(value),
    };

    // each rule item is the visible warning, gets a tick once its check passes
    if (popup) {
        const items = popup.querySelectorAll('.rule-item');
        items.forEach(function(item){
            const rule = item.getAttribute('data-rule');
            if (checks[rule]) {
                item.classList.add('rule-met');
            } else {
                item.classList.remove('rule-met');
            }
        });
        if (value.length === 0) {
            popup.style.display = 'none';
        } else if (passwordRulesAllMet()) {
            // hide once everything is satisfied so the form is uncluttered
            popup.style.display = 'none';
        } else if (passwordTouched) {
            popup.style.display = 'block';
        }
    }

    if (value.length > 0 && !passwordRulesAllMet()){
        password.classList.add('input-invalid');
        password.classList.remove('input-valid');
    }
    else if (passwordRulesAllMet()){
        password.classList.add('input-valid');
        password.classList.remove('input-invalid');
    }
    else {
        password.classList.remove('input-valid', 'input-invalid');
    }

    // confirm-password warning, only after the user has typed in that box
    if (confirmTouched && confirmValue.length > 0 && confirmValue !== value) {
        error.style.display = 'block';
        error.textContent = 'Passwords do not match.';
        confirmPassword.classList.add('input-invalid');
        confirmPassword.classList.remove('input-valid');
    } else if (confirmValue.length > 0 && confirmValue === value && passwordRulesAllMet()) {
        error.style.display = 'none';
        confirmPassword.classList.add('input-valid');
        confirmPassword.classList.remove('input-invalid');
    } else {
        error.style.display = 'none';
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
