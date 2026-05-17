// AJAX user search + follow/unfollow for the Following page.
// debounce pattern matches signup.js so the server isn't hammered on every keystroke.

let searchTimer = null;
// last query we actually sent, so out-of-order responses can be ignored
let lastQuerySent = '';

function csrfHeader() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.getAttribute('content') : '';
    return token ? { 'X-CSRFToken': token } : {};
}

function escapeHTML(str) {
    // tiny helper to keep usernames safe when injected into the DOM
    return String(str).replace(/[&<>"']/g, function(c){
        return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c];
    });
}

function renderResults(results, query) {
    const list = document.getElementById('searchResults');
    list.innerHTML = '';
    if (results.length === 0) {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-dark text-white';
        li.textContent = 'No users matched "' + query + '".';
        list.appendChild(li);
        return;
    }
    results.forEach(function(user){
        const li = document.createElement('li');
        li.className = 'list-group-item bg-dark text-white d-flex align-items-center';
        li.setAttribute('data-user-id', user.id);

        const img = document.createElement('img');
        img.src = '/static/images/avatars/' + encodeURIComponent(user.avatar) + '.png';
        img.alt = '';
        img.width = 32; img.height = 32;
        img.style.borderRadius = '50%';
        img.style.objectFit = 'cover';
        img.style.marginRight = '10px';
        li.appendChild(img);

        const name = document.createElement('span');
        name.className = 'flex-grow-1';
        name.innerHTML = escapeHTML(user.display_name);
        li.appendChild(name);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm ' + (user.is_followed ? 'btn-outline-light' : 'btn-light');
        btn.textContent = user.is_followed ? 'Unfollow' : 'Follow';
        btn.setAttribute('data-user-id', user.id);
        btn.setAttribute('data-username', user.username);
        btn.setAttribute('data-display-name', user.display_name);
        btn.setAttribute('data-avatar', user.avatar);
        btn.addEventListener('click', function(){
            if (btn.textContent === 'Follow') {
                doFollow(user.id, btn);
            } else {
                doUnfollow(user.id, btn);
            }
        });
        li.appendChild(btn);

        list.appendChild(li);
    });
}

function runSearch(query) {
    fetch('/api/users/search?q=' + encodeURIComponent(query))
        .then(function(res){ return res.json(); })
        .then(function(data){
            // ignore responses for stale queries so older requests don't overwrite newer ones
            if (query !== lastQuerySent) return;
            const status = document.getElementById('searchStatus');
            if (!data.ok) {
                status.style.display = 'block';
                status.textContent = data.reason === 'rate_limited'
                    ? 'Slow down a moment, then try again.'
                    : 'Search failed.';
                return;
            }
            status.style.display = 'none';
            renderResults(data.results, query);
        })
        .catch(function(){
            // network blip, just clear the list to be safe
            document.getElementById('searchResults').innerHTML = '';
        });
}

function onSearchInput() {
    const input = document.getElementById('userSearch');
    const status = document.getElementById('searchStatus');
    const value = input.value.trim();
    clearTimeout(searchTimer);
    if (value.length === 0) {
        document.getElementById('searchResults').innerHTML = '';
        status.style.display = 'none';
        lastQuerySent = '';
        return;
    }
    status.style.display = 'block';
    status.textContent = 'Searching...';
    searchTimer = setTimeout(function(){
        lastQuerySent = value;
        runSearch(value);
    }, 250);
}

function doFollow(userId, btn) {
    fetch('/api/follow', {
        method: 'POST',
        headers: Object.assign({ 'Content-Type': 'application/json' }, csrfHeader()),
        body: JSON.stringify({ user_id: userId }),
    })
    .then(function(res){ return res.json(); })
    .then(function(data){
        if (!data.ok) return;
        btn.textContent = 'Unfollow';
        btn.classList.remove('btn-light');
        btn.classList.add('btn-outline-light');
        // also reflect in the bottom list so the page is consistent without a full reload
        addToFollowingList(btn);
    });
}

function doUnfollow(userId, btn) {
    fetch('/api/unfollow', {
        method: 'POST',
        headers: Object.assign({ 'Content-Type': 'application/json' }, csrfHeader()),
        body: JSON.stringify({ user_id: userId }),
    })
    .then(function(res){ return res.json(); })
    .then(function(data){
        if (!data.ok) return;
        // search-result button flips back to Follow
        if (btn && btn.parentElement && btn.parentElement.parentElement
                && btn.parentElement.parentElement.id === 'searchResults') {
            btn.textContent = 'Follow';
            btn.classList.add('btn-light');
            btn.classList.remove('btn-outline-light');
        }
        removeFromFollowingList(userId);
    });
}

function addToFollowingList(srcBtn) {
    const list = document.getElementById('followingList');
    const empty = document.getElementById('followingEmpty');
    if (empty) empty.remove();
    const userId = srcBtn.getAttribute('data-user-id');
    if (list.querySelector('li[data-user-id="' + userId + '"]')) return;

    const li = document.createElement('li');
    li.className = 'list-group-item bg-dark text-white d-flex align-items-center';
    li.setAttribute('data-user-id', userId);

    const img = document.createElement('img');
    img.src = '/static/images/avatars/' + encodeURIComponent(srcBtn.getAttribute('data-avatar')) + '.png';
    img.alt = '';
    img.width = 32; img.height = 32;
    img.style.borderRadius = '50%';
    img.style.objectFit = 'cover';
    img.style.marginRight = '10px';
    li.appendChild(img);

    const name = document.createElement('span');
    name.className = 'flex-grow-1';
    name.innerHTML = escapeHTML(srcBtn.getAttribute('data-display-name'));
    li.appendChild(name);

    const off = document.createElement('button');
    off.type = 'button';
    off.className = 'btn btn-sm btn-outline-light unfollow-btn';
    off.textContent = 'Unfollow';
    off.setAttribute('data-user-id', userId);
    off.addEventListener('click', function(){ doUnfollow(parseInt(userId, 10), off); });
    li.appendChild(off);

    list.appendChild(li);
}

function removeFromFollowingList(userId) {
    const list = document.getElementById('followingList');
    const row = list.querySelector('li[data-user-id="' + userId + '"]');
    if (row) row.remove();
    if (list.children.length === 0) {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-dark text-white';
        li.id = 'followingEmpty';
        li.textContent = "You aren't following anyone yet.";
        list.appendChild(li);
    }
}

document.addEventListener('DOMContentLoaded', function(){
    const input = document.getElementById('userSearch');
    input.addEventListener('input', onSearchInput);

    // wire the server-rendered Unfollow buttons too, so they work without a reload
    document.querySelectorAll('#followingList .unfollow-btn').forEach(function(btn){
        btn.addEventListener('click', function(){
            const uid = parseInt(btn.getAttribute('data-user-id'), 10);
            doUnfollow(uid, btn);
        });
    });
});
