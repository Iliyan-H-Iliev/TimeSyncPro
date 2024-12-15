document.addEventListener('DOMContentLoaded', function () {
    function getCsrfToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        if (!csrfToken) {
            console.error("CSRF token not found.");
            return null;
        }
        return csrfToken;
    }

    function handleAbsenceDelete(absenceId) {
        if (!confirm("Are you sure you want to delete this absence?")) {
            return;
        }

        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            alert("Security token not found. Please refresh the page.");
            return;
        }

        fetch(`/api/absences/${absenceId}/delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
            .then(response => {
                return response.json().then(data => {
                    if (response.status === 403) {
                        throw new Error('You do not have permission to delete this absence.');
                    }
                    if (response.status === 404) {
                        throw new Error('Absence not found.');
                    }
                    if (!response.ok) {
                        throw new Error(data.error || 'Failed to delete absence.');
                    }
                    return data;
                });
            })
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert(error.message || "An unexpected error occurred");
            });
    }

    document.querySelectorAll('.holiday-status-button[data-action="delete"]').forEach(button => {
        button.addEventListener('click', function () {
            const absenceId = this.dataset.holidayId;
            handleAbsenceDelete(absenceId);
        });
    });
});