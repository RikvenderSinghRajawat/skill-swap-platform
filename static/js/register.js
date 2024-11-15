document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const usernameField = document.getElementById('username');
    const usernameError = document.getElementById('usernameError');

    registerForm.addEventListener('submit', (event) => {
        const username = usernameField.value;

        // Check for spaces in username
        if (username.includes(' ')) {
            event.preventDefault();  // Prevent form submission
            usernameError.textContent = 'Username cannot contain spaces.';
        } else {
            usernameError.textContent = '';  // Clear error message
        }
    });
});
