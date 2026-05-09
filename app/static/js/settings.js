// minimal client check on the new password fields, server-side wins either way
function validateSettingsPassword(){
    const newPw = document.getElementById('newPassword');
    const confirmPw = document.getElementById('confirmNewPassword');
    const error = document.getElementById('newPasswordError');
    if (!newPw || !confirmPw || !error) return;

    const value = newPw.value;
    const confirmValue = confirmPw.value;

    const hasLength = value.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(value);
    const hasNumber = /[0-9]/.test(value);
    const hasSymbol = /[!@#$%&*_]/.test(value);

    if (value.length > 0 && (!hasLength || !hasLetter || !hasNumber || !hasSymbol)){
        error.style.display = 'block';
        error.textContent = 'New password must be 8+ chars with a letter, number, and symbol (! @ # $ % & * _)';
        return;
    }
    if (confirmValue.length > 0 && confirmValue !== value){
        error.style.display = 'block';
        error.textContent = 'New passwords do not match.';
        return;
    }
    error.style.display = 'none';
    error.textContent = '';
}
