// backend/static/script.js

// ✅ Load partial page into #content
async function loadPage(pageName) {
    const contentDiv = document.getElementById('content');
    try {
        const response = await fetch(`/pages/${pageName}`); // Flask route
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        contentDiv.innerHTML = await response.text();

        // ✅ Re-execute any scripts inside the loaded partial
        const scripts = contentDiv.querySelectorAll('script');
        scripts.forEach(script => {
            const newScript = document.createElement('script');
            Array.from(script.attributes).forEach(attr =>
                newScript.setAttribute(attr.name, attr.value)
            );
            newScript.textContent = script.textContent;
            script.parentNode.replaceChild(newScript, script);
        });

        // ✅ Page-specific logic
        if (pageName === 'combined_view') {
            setTimeout(() => {
                if (typeof loadAbhishekData === 'function') {
                    loadAbhishekData(); // Defined in combined_view.html
                }
            }, 0);
        }

    } catch (error) {
        console.error('Error loading page:', error);
        contentDiv.innerHTML = '<p>Error loading page. Please try again.</p>';
    }
}

// ✅ Wrapper for button click — sets hash and loads page
function navigateTo(pageName) {
    if (pageName === 'home') {
        document.getElementById('content').innerHTML = `
            <h2>🙏 Welcome!</h2>
            <p>Use the above options to manage Bhakts, Abhisheks, and Sacred Rituals efficiently.</p>
        `;
    } else {
        fetch(`/pages/${pageName}`)
            .then(response => response.text())
            .then(html => {
                document.getElementById('content').innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading page:', error);
            });
    }
}


// ✅ Handle hash changes on back/forward/navigation
function handleHashChange() {
    const pageName = window.location.hash.substring(1); // Remove "#"
    if (pageName) {
        loadPage(pageName);
    }
}

// ✅ On first load
document.addEventListener('DOMContentLoaded', () => {
    handleHashChange(); // Load correct page if hash exists
});

// ✅ Listen to browser history changes
window.addEventListener('hashchange', handleHashChange);

// ✅ Example function to register Bhakt (from form in register_bhakt.html)
async function registerBhakt() {
    const form = document.getElementById('bhaktRegistrationForm');
    const formData = new FormData(form);
    const data = {
        name: formData.get('name'),
        mobile_number: formData.get('mobile_number'),
        address: formData.get('address'),
        gotra: formData.get('gotra'),
        email_address: formData.get('email_address'),
        abhishek_types: Array.from(
            form.querySelectorAll('input[name="abhishek_type"]:checked')
        ).map(cb => cb.value),
        start_date: formData.get('start_date'),
        validity_months: parseInt(formData.get('validity_months')) || 12
    };

    try {
        const response = await fetch('/bhakts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            form.reset();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error registering Bhakt:', error);
        alert('An error occurred. Please try again.');
    }
}
