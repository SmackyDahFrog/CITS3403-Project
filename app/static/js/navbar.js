document.addEventListener('DOMContentLoaded', function () {
    const displayName = sessionStorage.getItem('displayName') || 'Player';
    const avatar = sessionStorage.getItem('avatar') || null;

    const navDisplayName = document.getElementById('navDisplayName');
    if (navDisplayName) {
        navDisplayName.textContent = displayName;
    }

    const navProfileDisplay = document.getElementById('navProfileDisplay');
    if (navProfileDisplay) {
        if (avatar) {
            navProfileDisplay.innerHTML = `<img src="avatars/${avatar}.png" alt="Profile">`;
        } else {
            navProfileDisplay.textContent = displayName.charAt(0).toUpperCase();
        }
    }
});

function handleLogout() {
    sessionStorage.clear();
    window.location.href = 'MainPage.html';
}