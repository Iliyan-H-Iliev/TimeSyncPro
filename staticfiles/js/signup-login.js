    // JavaScript to handle label movement based on input focus and content
    document.querySelectorAll('.input-box input').forEach(function(input) {
        const inputBox = input.closest('.input-box');

        // Check input value on load in case of autofill
        if (input.value.trim() !== '') {
            inputBox.classList.add('input-filled');
        }

        // Add or remove 'input-filled' class based on input content
        input.addEventListener('input', function() {
            if (input.value.trim() !== '') {
                inputBox.classList.add('input-filled');
            } else {
                inputBox.classList.remove('input-filled');
            }
        });

        // Remove 'input-filled' class when input is empty and loses focus
        input.addEventListener('blur', function() {
            if (input.value.trim() === '') {
                inputBox.classList.remove('input-filled');
            }
        });
    });