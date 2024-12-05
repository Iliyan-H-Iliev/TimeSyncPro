document.addEventListener('DOMContentLoaded', function() {
    // Select all elements with the logout-link class
    const logoutLinks = document.querySelectorAll('.logout-link');

    // Add the event listener to each link
    logoutLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    });
});


function logout() {
    fetch('/sign_out/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        credentials: 'include'
    }).then(response => {
        if (response.ok) {
            window.location.href = '/sign_in/';
        }
    });
}