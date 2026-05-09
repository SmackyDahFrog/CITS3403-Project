// navbar.js — dropdown is handled by Bootstrap JS automatically.
// User data is injected server-side via Jinja2, no sessionStorage needed.

// Legacy logout handler kept for any old references, but logout now uses Flask route directly.
function handleLogout() {
    window.location.href = '/logout';
}