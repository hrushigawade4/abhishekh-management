// backend/static/script.js
async function loadPage(pageName) {
    const contentDiv = document.getElementById('content');
    try {
        const response = await fetch(`/pages/${pageName}`); // Flask route to serve HTML partials
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        contentDiv.innerHTML = await response.text();

        // Re-execute any scripts inside the newly loaded partial
        const scripts = contentDiv.querySelectorAll('script');
        scripts.forEach(script => {
            const newScript = document.createElement('script');
            Array.from(script.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
            newScript.textContent = script.textContent;
            script.parentNode.replaceChild(newScript, script);
        });

        // ✅ Custom logic after content is loaded
        if (pageName === 'combined_view') {
            setTimeout(() => {
                if (typeof loadAbhishekData === 'function') {
                    loadAbhishekData(); // This function is defined in combined_view.html
                }
            }, 0);
        }

    } catch (error) {
        console.error('Error loading page:', error);
        contentDiv.innerHTML = '<p>Error loading page. Please try again.</p>';
    }
}


// Example: Function to register a Bhakt (called from register_bhakt.html form)
async function registerBhakt() {
    const form = document.getElementById('bhaktRegistrationForm');
    const formData = new FormData(form);
    const data = {
        name: formData.get('name'),
        mobile_number: formData.get('mobile_number'),
        address: formData.get('address'),
        gotra: formData.get('gotra'),
        email_address: formData.get('email_address'),
        abhishek_types: Array.from(form.querySelectorAll('input[name="abhishek_type"]:checked')).map(cb => cb.value),
        start_date: formData.get('start_date'),
        validity_months: parseInt(formData.get('validity_months')) || 12
    };

    try {
        const response = await fetch('/bhakts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message);
            form.reset(); // Clear form
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error registering Bhakt:', error);
        alert('An error occurred. Please try again.');
    }
}

// Initial page load
document.addEventListener('DOMContentLoaded', () => {
    // Optionally load a default page or just show the welcome message
});

if (pageName === 'combined_view') {
    setTimeout(() => {
        if (typeof loadAbhishekData === 'function') {
            loadAbhishekData();
        }
    }, 0); // defer to next tick
}