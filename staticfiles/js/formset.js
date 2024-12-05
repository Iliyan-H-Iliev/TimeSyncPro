// document.addEventListener('DOMContentLoaded', function () {
//     // console.log("JavaScript Loaded");
//
//     const formsetContainer = document.getElementById('formset-container');
//     const addBlockButton = document.getElementById('add-block');
//     const rotationWeeksField = document.getElementById('id_rotation_weeks');
//     const totalFormsInput = document.querySelector('[name="blocks-TOTAL_FORMS"]');
//     const emptyFormTemplate = document.getElementById('empty-form-template')?.innerHTML;
//
//     if (!formsetContainer || !addBlockButton || !rotationWeeksField || !totalFormsInput || !emptyFormTemplate) {
//         console.error("Required DOM elements are missing");
//         return;
//     }
//
//     // Helper: Get Visible Forms (Exclude Deleted Forms)
//     function getVisibleForms() {
//         return Array.from(formsetContainer.children).filter((form) => {
//             const deleteField = form.querySelector('input[name$="-DELETE"]');
//             return form.style.display !== "none" && (!deleteField || !deleteField.checked);
//         });
//     }
//
//     // Helper: Update Week Numbers
//     function updateWeekNumbers() {
//         const visibleForms = getVisibleForms();
//         // console.log("Updating week numbers, total visible forms:", visibleForms.length);
//
//         visibleForms.forEach((form, index) => {
//             const weekHeader = form.querySelector('h4');
//             if (weekHeader) {
//                 weekHeader.textContent = `Week ${index + 1}`;
//             }
//         });
//     }
//
//     // Helper: Update Rotation Weeks
//     function updateRotationWeeks() {
//         const visibleForms = getVisibleForms();
//         const visibleCount = visibleForms.length;
//         rotationWeeksField.value = visibleCount; // Update rotation_weeks field
//         // console.log("Rotation weeks updated to:", visibleCount);
//     }
//
//     // Add New Block
//     addBlockButton.addEventListener('click', function () {
//         const currentForms = parseInt(totalFormsInput.value, 10); // Get the total number of forms (including hidden ones)
//         // console.log("Adding block. Current TOTAL_FORMS:", currentForms);
//
//         // Replace `__prefix__` with the new form index
//         const newFormHtml = emptyFormTemplate.replace(/__prefix__/g, currentForms);
//         const newFormDiv = document.createElement('div');
//         newFormDiv.classList.add('block-form');
//         newFormDiv.innerHTML = newFormHtml;
//
//         // Append the new form
//         formsetContainer.appendChild(newFormDiv);
//
//         // Update TOTAL_FORMS (this tracks the total number of forms including hidden ones)
//         totalFormsInput.value = currentForms + 1;
//
//         // Update week numbers and rotation weeks
//         updateWeekNumbers();
//         updateRotationWeeks();
//     });
//
//     // Remove Block
//     formsetContainer.addEventListener('click', function (event) {
//         if (event.target.classList.contains('remove-block')) {
//             const blockForm = event.target.closest('.block-form');
//             // console.log("Removing block:", blockForm);
//
//             // Mark for deletion if part of an existing formset
//             const deleteField = blockForm.querySelector('input[name$="-DELETE"]');
//             if (deleteField) {
//                 deleteField.checked = true; // Mark for deletion
//                 blockForm.style.display = 'none'; // Hide the form
//             } else {
//                 // Remove newly added form
//                 blockForm.remove();
//             }
//
//             // Update week numbers and rotation weeks
//             updateWeekNumbers();
//             updateRotationWeeks();
//         }
//     });
//
//     // Initialize Week Numbers and Rotation Weeks on Page Load
//     updateWeekNumbers();
//     updateRotationWeeks();
// });
//







document.addEventListener('DOMContentLoaded', function () {
    const formsetContainer = document.getElementById('formset-container');
    const addBlockButton = document.getElementById('add-block');
    const rotationWeeksField = document.getElementById('id_rotation_weeks');
    const totalFormsInput = document.querySelector('[name="blocks-TOTAL_FORMS"]');
    const emptyFormTemplate = document.getElementById('empty-form-template')?.innerHTML;
    const updateButton = document.getElementById('update-button'); // Button to disable
    const messageContainer = document.getElementById('message-container'); // Place to show messages

    if (!formsetContainer || !addBlockButton || !rotationWeeksField || !totalFormsInput || !emptyFormTemplate || !updateButton || !messageContainer) {
        console.error("Required DOM elements are missing");
        return;
    }

    // Helper: Get Visible Forms (Exclude Deleted Forms)
    function getVisibleForms() {
        return Array.from(formsetContainer.children).filter((form) => {
            const deleteField = form.querySelector('input[name$="-DELETE"]');
            return form.style.display !== "none" && (!deleteField || !deleteField.checked);
        });
    }

    // Helper: Update Week Numbers
    function updateWeekNumbers() {
        const visibleForms = getVisibleForms();

        visibleForms.forEach((form, index) => {
            const weekHeader = form.querySelector('h4');
            if (weekHeader) {
                weekHeader.textContent = `Week ${index + 1}`;
            }
        });
    }

    // Helper: Update Rotation Weeks
    function updateRotationWeeks() {
        const visibleForms = getVisibleForms();
        const visibleCount = visibleForms.length;
        rotationWeeksField.value = visibleCount; // Update rotation_weeks field

        if (visibleCount === 0) {
            // Disable the update button and show the error message
            updateButton.disabled = true;
            messageContainer.textContent = "You must have at least 1 rotation week.";
            messageContainer.style.display = "block";
        } else {
            // Enable the update button and hide the error message
            updateButton.disabled = false;
            messageContainer.style.display = "none";
        }
    }

    // Add New Block
    addBlockButton.addEventListener('click', function () {
        const currentForms = parseInt(totalFormsInput.value, 10); // Get the total number of forms (including hidden ones)

        // Replace `__prefix__` with the new form index
        const newFormHtml = emptyFormTemplate.replace(/__prefix__/g, currentForms);
        const newFormDiv = document.createElement('div');
        newFormDiv.classList.add('block-form');
        newFormDiv.innerHTML = newFormHtml;

        // Append the new form
        formsetContainer.appendChild(newFormDiv);

        // Update TOTAL_FORMS (this tracks the total number of forms including hidden ones)
        totalFormsInput.value = currentForms + 1;

        // Update week numbers and rotation weeks
        updateWeekNumbers();
        updateRotationWeeks();
    });

    // Remove Block
    formsetContainer.addEventListener('click', function (event) {
        if (event.target.classList.contains('remove-block')) {
            const blockForm = event.target.closest('.block-form');

            // Mark for deletion if part of an existing formset
            const deleteField = blockForm.querySelector('input[name$="-DELETE"]');
            if (deleteField) {
                deleteField.checked = true; // Mark for deletion
                blockForm.style.display = 'none'; // Hide the form
            } else {
                // Remove newly added form
                blockForm.remove();
            }

            // Update week numbers and rotation weeks
            updateWeekNumbers();
            updateRotationWeeks();
        }
    });

    // Initialize Week Numbers and Rotation Weeks on Page Load
    updateWeekNumbers();
    updateRotationWeeks();
});