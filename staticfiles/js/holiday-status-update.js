document.addEventListener("DOMContentLoaded", function () {
    // Constants to match Django model's StatusChoices
    const STATUS = {
        PENDING: 'pending',
        APPROVED: 'approved',
        DENIED: 'denied',
        CANCELLED: 'cancelled'  // Note: matches Django model's spelling
    };

    // Function to fetch CSRF token
    function getCsrfToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        if (!csrfToken) {
            console.error("CSRF token not found.");
            return null;
        }
        return csrfToken;
    }

    // Function to handle holiday status updates
    function handleHolidayStatusUpdate(holidayId, action) {
        // Determine confirmation message based on action
        const confirmMessages = {
            [STATUS.CANCELLED]: "Are you sure you want to cancel this holiday request?",
            [STATUS.APPROVED]: "Are you sure you want to approve this holiday request?",
            [STATUS.DENIED]: "Are you sure you want to deny this holiday request?"
        };

        const confirmMessage = confirmMessages[action];
        if (!confirmMessage || !confirm(confirmMessage)) {
            return;
        }

        // Get denial reason if needed
        let reviewReason = null;
        if (action === STATUS.DENIED) {
            reviewReason = prompt("Please provide a reason for denial:");
            if (!reviewReason) {
                alert("A reason is required when denying a holiday request.");
                return;
            }
        }

        // Get CSRF token
        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            alert("Security token not found. Please refresh the page and try again.");
            return;
        }

        // Prepare request data
        const requestData = {
            status: action
        };

        if (reviewReason) {
            requestData.review_reason = reviewReason;
        }

        // Make API request
        fetch(`/api/holidays/${holidayId}/update-status/`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    if (data.error && typeof data.error === 'object') {
                        // Handle case where error is an object with multiple validation errors
                        throw new Error(Object.values(data.error).flat().join('\n'));
                    }
                    throw new Error(data.error || "An error occurred while processing your request.");
                }
                return data;
            });
        })
        .then(data => {
            alert(data.message);
            location.reload();
        })
        .catch(error => {
            console.error("Error:", error);
            alert(error.message || "An unexpected error occurred. Please try again.");
        });
    }

    // Attach event listeners to all holiday status buttons
    document.querySelectorAll(".holiday-status-button").forEach(button => {
        button.addEventListener("click", function() {
            const holidayId = this.dataset.holidayId;
            const action = this.dataset.action;

            // Validate the action value
            const validActions = Object.values(STATUS);
            if (!validActions.includes(action)) {
                console.error(`Invalid action: ${action}`);
                alert("Invalid action requested.");
                return;
            }

            handleHolidayStatusUpdate(holidayId, action);
        });
    });
});

// document.addEventListener("DOMContentLoaded", function () {
//     // Function to fetch CSRF token
//     function getCsrfToken() {
//         const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
//         if (!csrfToken) {
//             console.error("CSRF token not found.");
//         }
//         return csrfToken;
//     }
//
//     document.querySelectorAll(".holiday-status-button").forEach(button => {
//         button.addEventListener("click", function () {
//             const holidayId = this.dataset.holidayId;
//             const action = this.dataset.action; // 'approved', 'denied', 'cancelled'
//             const reviewReason = action === "denied" ? prompt("Provide a reason for denial:") : null;
//
//             if (action === "denied" && !reviewReason) {
//                 alert("Denial requires a review reason.");
//                 return;
//             }
//
//             fetch(`/api/holidays/${holidayId}/update-status/`, {
//                 method: "PATCH",
//                 headers: {
//                     "Content-Type": "application/json",
//                     "X-CSRFToken": getCsrfToken() // Fetch CSRF token dynamically
//                 },
//                 body: JSON.stringify({
//                     status: action,
//                     review_reason: reviewReason,
//                 })
//             })
//                 .then(response => {
//                     if (!response.ok) {
//                         return response.json().then(data => {
//                             throw new Error(data.error || "An error occurred.");
//                         });
//                     }
//                     return response.json();
//                 })
//                 .then(data => {
//                     alert(data.message);
//                     location.reload(); // Refresh to reflect changes
//                 })
//                 .catch(error => {
//                     console.error("Error:", error);
//                     alert(error.message);
//                 });
//         });
//     });
// });