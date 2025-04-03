document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript is ready!");

    // Element references
    const signupButton = document.getElementById("openSignupModal");
    const loginButton = document.getElementById("openLoginModal");
    const signupModal = document.getElementById("signupModal");
    const loginModal = document.getElementById("loginModal");
    const closeSignupModal = signupModal?.querySelector(".close");
    const closeLoginModal = loginModal?.querySelector(".close");
    const signupForm = signupModal?.querySelector("form");
    const loginForm = loginModal?.querySelector("form");
    const messagesDiv = document.querySelector(".messages");
    const isAuthenticated = "{{ user.is_authenticated|yesno:'true,false' }}";

    // Helper: Open and close modals
    const openModal = (modal) => {
        if (modal) {
            modal.style.display = "block";
            console.log(`${modal.id} opened.`);
        }
    };

    const closeModal = (modal, form = null) => {
        if (modal) {
            modal.style.display = "none";
            console.log(`${modal.id} closed.`);
            form?.reset();
            resetFieldBorders(form);
        }
    };

    const resetFieldBorders = (form) => {
        form?.querySelectorAll("input").forEach(input => {
            input.style.borderColor = "";
        });
    };

    // Form validation function
    const validateForm = (form) => {
        let isValid = true;
        form.querySelectorAll("input[required]").forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = "red";
                isValid = false;
            } else {
                input.style.borderColor = "";
            }
        });
        return isValid;
    };

    // Event listeners for modals
    signupButton?.addEventListener("click", () => openModal(signupModal));
    loginButton?.addEventListener("click", () => openModal(loginModal));
    closeSignupModal?.addEventListener("click", () => closeModal(signupModal, signupForm));
    closeLoginModal?.addEventListener("click", () => closeModal(loginModal, loginForm));

    loginModal?.querySelector("p a")?.addEventListener("click", () => {
        closeModal(loginModal, loginForm);
        openModal(signupModal);
    });

    // Close modals when clicking outside
    window.addEventListener("click", (event) => {
        if (event.target === signupModal) closeModal(signupModal, signupForm);
        if (event.target === loginModal) closeModal(loginModal, loginForm);
    });

    // Signup form submission with AJAX
    signupForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (validateForm(signupForm)) {
            try {
                const formData = new FormData(signupForm);
                const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
                const response = await fetch(signupForm.action, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: formData,
                });

                const data = await response.json();
                handleSignupResponse(data);
            } catch (error) {
                console.error("Error during signup:", error);
                displayErrors({ error: ["An error occurred during signup. Please try again."] });
            }
        } else {
            alert("Please fill in all required fields.");
        }
    });

    // Login form submission with AJAX
    loginForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (validateForm(loginForm)) {
            try {
                const formData = new FormData(loginForm);
                const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

                const response = await fetch("/login/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                    },
                    body: formData,
                });

                const data = await response.json();
                handleLoginResponse(data);
            } catch (error) {
                console.error("Error during login:", error);
                displayErrors({ error: ["An error occurred during login. Please try again."] });
            }
        } else {
            alert("Please fill in all required fields.");
        }
    });

    // Handle signup response
    const handleSignupResponse = (data) => {
        if (data.success) {
            alert("Signup successful! Redirecting to login...");
            closeModal(signupModal);
            openModal(loginModal);
        } else {
            displayErrors(data.errors);
        }
    };

    // Handle login response
    const handleLoginResponse = (data) => {
        if (data.success) {
            const redirectUrl = data.redirect || "/dashboard";  // Fallback for redirect
            window.location.href = redirectUrl;
        } else {
            displayErrors(data.errors || { error: ["Invalid login credentials."] });
        }
    };

    // Display error messages
    const displayErrors = (errors) => {
        messagesDiv.innerHTML = "";
        if (Array.isArray(errors)) {
            errors.forEach(createErrorMessage);
        } else {
            Object.entries(errors).forEach(([field, messages]) => {
                messages.forEach(message => createErrorMessage(`${field}: ${message}`));
            });
        }
    };

    // Create error message elements
    const createErrorMessage = (message) => {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = message;
        messageDiv.classList.add("error-message");
        messagesDiv.appendChild(messageDiv);
    };

    // Redirect based on authentication
    const checkAuthAndRedirect = (serviceName) => {
        if (isAuthenticated === "true") {
            window.location.href = `/${serviceName}`;
        } else {
            alert("You need to log in to access this service.");
            openModal(loginModal);
        }
    };

    // Adding click events to service cards
    const serviceCards = document.querySelectorAll('.service-card');
    serviceCards.forEach(card => {
        card.addEventListener('click', () => {
            const serviceName = card.querySelector('h3').textContent.toLowerCase().replace(/\s+/g, '-');
            checkAuthAndRedirect(serviceName);
        });
    });
});

// Example JavaScript for interactive elements, dropdowns, etc.
document.addEventListener('DOMContentLoaded', function() {
    // Example of dropdown toggle logic
    document.querySelectorAll('.menu-item').forEach(function(item) {
        item.addEventListener('mouseover', function() {
            this.querySelector('.dropdown').style.display = 'block';
        });
        item.addEventListener('mouseout', function() {
            this.querySelector('.dropdown').style.display = 'none';
        });
    });
});
