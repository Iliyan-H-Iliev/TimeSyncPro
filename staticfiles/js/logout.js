document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from meta tag
    const csrftoken = document.querySelector('meta[name="csrf-token"]').content;

    // Select all elements with the logout-link class
    const logoutLinks = document.querySelectorAll('.logout-link');

    // Add the event listener to each link
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            logout(csrftoken);
        });
    });
});

function logout(csrftoken) {
    fetch('/sign-out/', {  // Changed from /sign_out/ to /sign-out/
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    }).then(response => {
        if (response.ok) {
            window.location.href = '/login/';
        }
    }).catch(error => {
        console.error('Logout error:', error);
    });
}