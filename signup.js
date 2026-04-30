function validateUsername() {
    const input = document.getElementById('username');
    const error = document.getElementById('usernameError');
    const value = input.value.trim();

    if (value.length>0 && value.length<4){
        error.style.display = 'block';
        input.classList.add('input-invalid'); 
        input.classList.remove('input-valid');
    }
    else if (value.length >= 4){
        error.style.display = 'none';
        input.classList.add('input-valid');
        input.classList.remove('input-invalid');
    }
    else{
        error.style.display = 'none';
        input.classList.remove('input-valid', 'input-invalid');
    }
}

function validatePasswords(){
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');
    const error = document.getElementById('passwordError');
    const value = password.value;
    const confirmValue = confirmPassword.value;

    const hasLength = value.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    const hasSymbol = /[!@#$%&*_]/.test(value);

    if (value.length > 0 && (!hasLength || !hasLetter || !hasNumber || !hasSymbol)){
        error.style.display = 'block';
        error.textContent = 'Password must be 8+ characters with a letter, number, and symbol(! @ # $ % & * _)';
        password.classList.add('input-invalid');
        password.classList.remove('input-valid');
    }
    else if (value.length > 8 && hasLetter && hasNumber && hasSymbol){
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
}

function handleSignup() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    const hasLength = password.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSymbol = /[!@#$%&*_]/.test(password);

    if (!username) {
        alert('Please enter a username.');
        return;
    }

    if (username.length < 4) {
        alert('Username must be at least 4 characters.');
        return;
    }

    if (!hasLength || !hasLetter || !hasNumber || !hasSymbol) {
        alert('Password must be 8+ characters with a letter, number, and symbol (! @ # $ % & * _)');
        return;
    }

    if (password !== confirmPassword) {
        alert('Passwords do not match.');
        return;
    }

    // Save username to sessionStorage for use on other pages
    sessionStorage.setItem('username', username);

    // Redirect to customisation page
    window.location.href = 'customisation.html';
}