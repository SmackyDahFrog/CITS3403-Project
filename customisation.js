/*
customisation.js- handles the avatar selection and saving profile
*/

function selectAvatar(el, avatarId){
    // remove selected from all avatars first
    document.querySelectorAll('.avatar-option img').forEach(img => {
        img.classList.remove('selected');
    });

    // mark the clicked one as selected
    el.classList.add('selected');
    document.getElementById('selectedAvatar').value = avatarId;
}

function handleCustomisation() {
    const displayName = document.getElementById('displayName').value.trim();
    const avatar = document.getElementById('selectedAvatar').value;

    if(!displayName) {
        alert('Please enter a display name.');
        return;
    }

    //save to sessionStorage for navbar and leaderboard to use
    sessionStorage.setItem('displayName', displayName);
    sessionStorage.setItem('avatar', avatar);

    //send them to the game selection page
    window.location.href = 'stages.html';
}