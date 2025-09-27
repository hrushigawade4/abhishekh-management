// import { faker } from '@faker-js/faker';

class BhaktManagementSystem {
    constructor() {
        this.bhakts = [];
        this.sacredDates = [];
        this.currentPage = 'dashboard';
        this.init();
    }

    async init() {
        this.setupNavigation();
        this.setupForms();
        this.setupModals();
        this.setupEventListeners();
        await this.fetchAbhishekTypes();
        await this.loadBhakts();
        await this.loadSacredDates();
        this.updateDashboard();
        this.populateYearSelector();
        this.setDefaultDate();
        this.setupLabelEvents(); // <-- Added here
    }

    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        const pages = document.querySelectorAll('.page');

        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetPage = btn.dataset.page;
                navButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                pages.forEach(page => page.classList.remove('active'));
                document.getElementById(targetPage).classList.add('active');
                this.currentPage = targetPage;
                this.loadPageData(targetPage);
            });
        });
    }

    setupForms() {
        const registerForm = document.getElementById('register-form');
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.registerBhakt(new FormData(registerForm));
        });

        const sacredDateForm = document.getElementById('sacred-date-form');
        sacredDateForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addSacredDate(new FormData(sacredDateForm));
        });
    }

    setupModals() {
        const modals = document.querySelectorAll('.modal');
        const closeButtons = document.querySelectorAll('.close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.modal').style.display = 'none';
            });
        });
        window.addEventListener('click', (e) => {
            modals.forEach(modal => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    setupEventListeners() {
         document.getElementById('add-sacred-date-btn').addEventListener('click', () => {
        this.fetchSacredAbhishekTypes();
        document.getElementById('sacred-date-modal').style.display = 'block';
    });
        document.getElementById('bhakt-search').addEventListener('input', (e) => {
            this.searchBhakts(e.target.value);
        });
        document.getElementById('generate-schedule').addEventListener('click', () => {
            this.generateSchedule();
        });
        document.getElementById('export-csv').addEventListener('click', () => {
            this.exportCSV();
        });
        document.getElementById('export-html').addEventListener('click', () => {
            this.exportHTML();
        });
         document.getElementById('export-bhakts').addEventListener('click', () => {
        window.open('/export/bhakts', '_blank');
    });
    
     document.getElementById('show-expired-bhakts').addEventListener('click', async () => {
        try {
            const response = await fetch('/bhakts/expired_last_month');
            if (!response.ok) throw new Error('Failed to fetch expired bhakts');
            const expiredBhakts = await response.json();
            const tbody = document.getElementById('bhakts-tbody');
            if (tbody) {
                tbody.innerHTML = expiredBhakts.map(bhakt => this.createBhaktRow(bhakt)).join('');
            }
            // Optionally, switch to the Manage Bhakts page
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            document.getElementById('bhakts').classList.add('active');
        } catch (error) {
            alert('Error loading expired bhakts: ' + error.message);
        }
    });
     document.getElementById('add-new-abhishek-type').addEventListener('click', () => {
        const newTypeInput = document.getElementById('new-abhishek-type');
        const select = document.getElementById('sacred-abhishek-type');
        const newType = newTypeInput.value.trim();
        if (newType) {
            // Add new option to select and select it
            const option = document.createElement('option');
            option.value = newType;
            option.textContent = newType;
            select.appendChild(option);
            select.value = newType;
            newTypeInput.value = '';
        }
    });

    document.getElementById('export-filtered-csv').addEventListener('click', () => {
    const month = parseInt(document.getElementById('schedule-month').value);
    const year = parseInt(document.getElementById('schedule-year').value);
    const abhishekType = document.getElementById('abhishek-type-filter').value;
    if (!abhishekType) {
        alert('Please select an Abhishek Type.');
        return;
    }
    window.open(`/export/monthly_schedule_filtered?month=${month}&year=${year}&abhishek_type=${encodeURIComponent(abhishekType)}`, '_blank');
});

    document.getElementById('send-db-backup').addEventListener('click', async () => {
    const email = document.getElementById('backup-email').value.trim();
    if (!email) {
        alert('Please enter a Gmail address.');
        return;
    }
    const adminPassword = prompt('Enter admin password for sending backup:');
    if (!adminPassword) return;
    try {
        const response = await fetch('/send_db_backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, admin_password: adminPassword })
        });
        const result = await response.json();
        if (response.ok) {
            alert(result.message || 'Backup sent!');
        } else {
            alert(result.error || 'Failed to send backup.');
        }
    } catch (error) {
        alert('Error sending backup: ' + error.message);
    }
});

    // document.getElementById('print-schedule').addEventListener('click', () => {
    // window.print();
    // });

    document.getElementById('show-expiring-soon-bhakts').addEventListener('click', async () => {
    try {
        const response = await fetch('/bhakts/expiring_soon');
        if (!response.ok) throw new Error('Failed to fetch expiring soon bhakts');
        const expiringBhakts = await response.json();
        const tbody = document.getElementById('bhakts-tbody');
        if (tbody) {
            tbody.innerHTML = expiringBhakts.map(bhakt => this.createBhaktRow(bhakt)).join('');
        }
        // Optionally, switch to the Manage Bhakts page
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        document.getElementById('bhakts').classList.add('active');
    } catch (error) {
        alert('Error loading expiring soon bhakts: ' + error.message);
    }
});

    document.getElementById('export-full-schedule').addEventListener('click', () => {
    const month = document.getElementById('schedule-month').value;
    const year = document.getElementById('schedule-year').value;
    window.open(`/export/monthly_schedule_full?month=${month}&year=${year}`, '_blank');
});

document.getElementById('backup-db').addEventListener('click', () => {
    const adminPassword = prompt('Enter admin password for backup:');
    if (!adminPassword) return;
    window.open(`/backup_db?admin_password=${encodeURIComponent(adminPassword)}`, '_blank');
});

document.getElementById('restore-db-btn').addEventListener('click', () => {
    document.getElementById('restore-db-file').click();
});

document.getElementById('restore-db-file').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const adminPassword = prompt('Enter admin password for restore:');
    if (!adminPassword) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('admin_password', adminPassword);
    try {
        const response = await fetch('/restore_db', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        alert(result.message || 'Database restored!');
        window.location.reload();
    } catch (error) {
        alert('Error restoring database: ' + error.message);
    }
});

const combinedSearch = document.getElementById('combined-search');
    if (combinedSearch) {
        combinedSearch.addEventListener('input', (e) => {
            this.searchCombinedView(e.target.value);
        });
    }

}

    async loadBhakts() {
        try {
            const response = await fetch('/bhakts');
            if (!response.ok) throw new Error('Failed to fetch bhakts');
            this.bhakts = await response.json();
            const tbody = document.getElementById('bhakts-tbody');
            if (tbody) {
                tbody.innerHTML = this.bhakts.map(bhakt => this.createBhaktRow(bhakt)).join('');
            }
        } catch (error) {
            alert('Error loading bhakts: ' + error.message);
        }
    }

    async loadSacredDates() {
        try {
            const response = await fetch('/sacred_dates');
            if (!response.ok) throw new Error('Failed to fetch sacred dates');
            this.sacredDates = await response.json();
            const tbody = document.getElementById('sacred-dates-tbody');
            if (tbody) {
                tbody.innerHTML = this.sacredDates.map(date => `
                    <tr>
                        <td>${date.abhishek_type}</td>
                        <td>${this.formatDate(date.date)}</td>
                        <td>${this.getDayOfWeek(date.date)}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="action-btn btn-secondary" onclick="window.bhaktSystem.editSacredDate(${date.id})">Edit</button>
                                <button class="action-btn btn-danger" onclick="window.bhaktSystem.deleteSacredDate(${date.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (error) {
            alert('Error loading sacred dates: ' + error.message);
        }
    }

    loadPageData(page) {
        switch (page) {
            case 'dashboard':
                this.updateDashboard();
                break;
            case 'bhakts':
                this.loadBhakts();
                break;
            case 'sacred-dates':
                this.loadSacredDates();
                break;
            case 'combined':
                this.loadCombinedView();
                break;
        }
    }

    loadCombinedView() {
    this.searchCombinedView('');
}

    async registerBhakt(formData) {
        try {
            const abhishekTypes = Array.from(document.querySelectorAll('#abhishek-types input:checked'))
                .map(cb => cb.value);

            if (abhishekTypes.length === 0) {
                alert('Please select at least one Abhishek type');
                return;
            }

            const payload = {
                name: formData.get('name'),
                mobile_number: formData.get('mobile'),
                email_address: formData.get('email'),
                gotra: formData.get('gotra'),
                address: formData.get('address'),
                abhishek_types: abhishekTypes,
                start_date: formData.get('start_date'),
                validity_months: parseInt(formData.get('validity_months'))
            };

            const response = await fetch('/bhakts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to register bhakt');

            alert('Bhakt registered successfully!');
            document.getElementById('register-form').reset();
            await this.loadBhakts();
            this.updateDashboard();
        } catch (error) {
            alert('Error registering bhakt: ' + error.message);
        }
    }

    async fetchAbhishekTypes() {
    try {
        const response = await fetch('/abhishek_types');
        if (!response.ok) throw new Error('Failed to fetch abhishek types');
        const types = await response.json();
        const container = document.getElementById('abhishek-types');
        if (container) {
            container.innerHTML = types.map(type => `
                <label>
                    <input type="checkbox" value="${type}"> ${type}
                </label>
            `).join('');
        }
    } catch (error) {
        console.error('Error fetching abhishek types:', error);
    }
}

    async addSacredDate(formData) {
        try {
            const payload = {
                abhishek_type: formData.get('abhishek_type'),
                date: formData.get('date')
            };

            const response = await fetch('/sacred_dates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to add sacred date');

            alert('Sacred date added successfully!');
            document.getElementById('sacred-date-form').reset();
            document.getElementById('sacred-date-modal').style.display = 'none';
            await this.loadSacredDates();
        } catch (error) {
            alert('Error adding sacred date: ' + error.message);
        }
    }

    updateDashboard() {
        const now = new Date();
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

        const totalBhakts = this.bhakts.length;
        const activeSubscriptions = this.bhakts.filter(b => new Date(b.expiration_date) > now).length;
        const sacredDatesCount = this.sacredDates.length;
        const expiringSoon = this.bhakts.filter(bhakt => {
            const expDate = new Date(bhakt.expiration_date);
            return expDate > now && expDate <= thirtyDaysFromNow;
        }).length;

        document.getElementById('total-bhakts').textContent = totalBhakts;
        document.getElementById('active-subscriptions').textContent = activeSubscriptions;
        document.getElementById('sacred-dates-count').textContent = sacredDatesCount;
        document.getElementById('expiring-soon').textContent = expiringSoon;

        this.updateRecentActivity();
    }

    updateRecentActivity() {
        const activityList = document.getElementById('recent-activity-list');
        const recentBhakts = this.bhakts
            .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
            .slice(0, 5);

        activityList.innerHTML = recentBhakts.map(bhakt => `
            <div class="activity-item">
                <div class="activity-time">${this.formatDate(bhakt.start_date)}</div>
                <div class="activity-description">New registration: ${bhakt.name}</div>
            </div>
        `).join('');
    }

    createBhaktRow(bhakt) {
        const status = this.getBhaktStatus(bhakt.expiration_date);
        return `
            <tr>
                <td>${bhakt.name}</td>
                <td>${bhakt.mobile_number || bhakt.mobile}</td>
                <td>${bhakt.gotra || '-'}</td>
                <td>${Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types.join(', ') : bhakt.abhishek_types}</td>
                <td>${this.formatDate(bhakt.expiration_date)}</td>
                <td><span class="status-badge ${status.class}">${status.text}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn btn-secondary" onclick="window.bhaktSystem.editBhakt(${bhakt.id})">Edit</button>
                        <button class="action-btn btn-success" onclick="window.bhaktSystem.renewBhakt(${bhakt.id})">Renew</button>
                        <button class="action-btn btn-danger" onclick="window.bhaktSystem.deleteBhakt(${bhakt.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }

    getBhaktStatus(expirationDate) {
        const now = new Date();
        const expDate = new Date(expirationDate);
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

        if (expDate < now) {
            return { text: 'Expired', class: 'status-expired' };
        } else if (expDate <= thirtyDaysFromNow) {
            return { text: 'Expiring Soon', class: 'status-expiring' };
        } else {
            return { text: 'Active', class: 'status-active' };
        }
    }

    searchBhakts(query) {
        const filtered = this.bhakts.filter(bhakt =>
            bhakt.name.toLowerCase().includes(query.toLowerCase()) ||
            (bhakt.mobile_number || bhakt.mobile).includes(query) ||
            (bhakt.email_address || bhakt.email || '').toLowerCase().includes(query.toLowerCase())
        );
        const tbody = document.getElementById('bhakts-tbody');
        if (tbody) {
            tbody.innerHTML = filtered.map(bhakt => this.createBhaktRow(bhakt)).join('');
        }
    }

   async editBhakt(id) {
    const bhakt = this.bhakts.find(b => b.id === id);
    if (!bhakt) return;

    // Fetch all available types from backend
    const response = await fetch('/abhishek_types');
    const allTypes = await response.json();

    // Prepare checked types
    const bhaktTypes = Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types : bhakt.abhishek_types.split(',');

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <form id="edit-bhakt-form" class="form">
            <div class="form-group">
                <label for="edit-name">Name *</label>
                <input type="text" id="edit-name" name="name" value="${bhakt.name}" required>
            </div>
            <div class="form-group">
                <label for="edit-mobile">Mobile *</label>
                <input type="tel" id="edit-mobile" name="mobile" value="${bhakt.mobile_number || bhakt.mobile}" required>
            </div>
            <div class="form-group">
                <label for="edit-email">Email</label>
                <input type="email" id="edit-email" name="email" value="${bhakt.email_address || bhakt.email || ''}">
            </div>
            <div class="form-group">
                <label for="edit-gotra">Gotra</label>
                <input type="text" id="edit-gotra" name="gotra" value="${bhakt.gotra || ''}">
            </div>
            <div class="form-group">
                <label for="edit-address">Address *</label>
                <textarea id="edit-address" name="address" required>${bhakt.address}</textarea>
            </div>
            <div class="form-group">
                <label>Abhishek Types *</label>
                <div class="checkbox-group" id="edit-abhishek-types">
                    ${allTypes.map(type => `
                        <label>
                            <input type="checkbox" value="${type}" ${bhaktTypes.includes(type) ? 'checked' : ''}> ${type}
                        </label>
                    `).join('')}
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Update Bhakt</button>
        </form>
    `;

    document.getElementById('modal-title').textContent = 'Edit Bhakt';
    document.getElementById('edit-modal').style.display = 'block';

    document.getElementById('edit-bhakt-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);

        const abhishekTypes = Array.from(document.querySelectorAll('#edit-abhishek-types input:checked'))
            .map(cb => cb.value);

        const payload = {
            name: formData.get('name'),
            mobile_number: formData.get('mobile'),
            email_address: formData.get('email'),
            gotra: formData.get('gotra'),
            address: formData.get('address'),
            abhishek_types: abhishekTypes
        };

        try {
            const response = await fetch(`/bhakts/${bhakt.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to update bhakt');
            document.getElementById('edit-modal').style.display = 'none';
            alert('Bhakt updated successfully!');
            await this.loadBhakts();
        } catch (error) {
            alert('Error updating bhakt: ' + error.message);
        }
    });
}

    async fetchSacredAbhishekTypes() {
    try {
        const response = await fetch('/abhishek_types');
        if (!response.ok) throw new Error('Failed to fetch abhishek types');
        const types = await response.json();
        const select = document.getElementById('sacred-abhishek-type');
        if (select) {
            select.innerHTML = '<option value="">Select type</option>' +
                types.map(type => `<option value="${type}">${type}</option>`).join('');
        }
    } catch (error) {
        console.error('Error fetching abhishek types:', error);
    }
}

async renewBhakt(id) {
    const bhakt = this.bhakts.find(b => b.id === id);
    if (!bhakt) return;

    const months = prompt('Enter validity months:', '12');
    if (!months || isNaN(months)) return;

    try {
        const response = await fetch(`/renew_bhakt/${bhakt.id}`, {  // Changed endpoint
            method: 'POST',  // Changed to POST
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ validity_months: parseInt(months) })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Failed to renew bhakt');
        alert('Bhakt subscription renewed successfully!');
        await this.loadBhakts();
        this.updateDashboard();
    } catch (error) {
        alert('Error renewing bhakt: ' + error.message);
    }
}

   async deleteBhakt(id) {
    if (confirm('Are you sure you want to delete this bhakt?')) {
        if (confirm('This action cannot be undone. Do you really want to delete this bhakt?')) {
            try {
                const response = await fetch(`/bhakts/${id}`, { method: 'DELETE' });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Failed to delete bhakt');
                alert('Bhakt deleted successfully!');
                await this.loadBhakts();
                this.updateDashboard();
            } catch (error) {
                alert('Error deleting bhakt: ' + error.message);
            }
        }
    }
}

   async editSacredDate(id) {
    const sacredDate = this.sacredDates.find(d => d.id === id);
    if (!sacredDate) return;

    // Fetch all available types from backend
    const response = await fetch('/abhishek_types');
    const allTypes = await response.json();

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <form id="edit-sacred-date-form" class="form">
            <div class="form-group">
                <label for="edit-abhishek-type">Abhishek Type *</label>
                <select id="edit-abhishek-type" name="abhishek_type" required>
                    <option value="">Select type</option>
                    ${allTypes.map(type => `
                        <option value="${type}" ${sacredDate.abhishek_type === type ? 'selected' : ''}>${type}</option>
                    `).join('')}
                </select>
                <div style="margin-top:8px;">
                    <input type="text" id="edit-new-abhishek-type" placeholder="Add new type (optional)">
                    <button type="button" id="edit-add-new-abhishek-type" class="btn btn-secondary" style="margin-left:8px;">Add</button>
                </div>
            </div>
            <div class="form-group">
                <label for="edit-date">Date *</label>
                <input type="date" id="edit-date" name="date" value="${sacredDate.date}" required>
            </div>
            <button type="submit" class="btn btn-primary">Update Sacred Date</button>
        </form>
    `;

    document.getElementById('modal-title').textContent = 'Edit Sacred Date';
    document.getElementById('edit-modal').style.display = 'block';

    // Handler to add new type to dropdown
    document.getElementById('edit-add-new-abhishek-type').addEventListener('click', () => {
        const newTypeInput = document.getElementById('edit-new-abhishek-type');
        const select = document.getElementById('edit-abhishek-type');
        const newType = newTypeInput.value.trim();
        if (newType) {
            const option = document.createElement('option');
            option.value = newType;
            option.textContent = newType;
            select.appendChild(option);
            select.value = newType;
            newTypeInput.value = '';
        }
    });

    document.getElementById('edit-sacred-date-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);

        const payload = {
            abhishek_type: formData.get('abhishek_type'),
            date: formData.get('date')
        };

        try {
            const response = await fetch(`/sacred_dates/${sacredDate.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to update sacred date');
            document.getElementById('edit-modal').style.display = 'none';
            alert('Sacred date updated successfully!');
            await this.loadSacredDates();
        } catch (error) {
            alert('Error updating sacred date: ' + error.message);
        }
    });

    
}


    async deleteSacredDate(id) {
        if (confirm('Are you sure you want to delete this sacred date?')) {
            try {
                const response = await fetch(`/sacred_dates/${id}`, { method: 'DELETE' });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Failed to delete sacred date');
                alert('Sacred date deleted successfully!');
                await this.loadSacredDates();
            } catch (error) {
                alert('Error deleting sacred date: ' + error.message);
            }
        }
    }

    searchCombinedView(query) {
    query = query.trim().toLowerCase();
    // Prepare the combined data as in loadCombinedView
    const activeBhakts = this.bhakts.filter(bhakt =>
        new Date(bhakt.expiration_date) > new Date()
    );
    let html = '<div class="combined-section">';
    html += '<h3>Active Bhakts and Their Sacred Dates</h3>';

    activeBhakts.forEach(bhakt => {
        const relevantDates = this.sacredDates.filter(date =>
            (Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types : bhakt.abhishek_types.split(',')).includes(date.abhishek_type)
        );
        // Check if any field matches the query
        const match =
            bhakt.name.toLowerCase().includes(query) ||
            (bhakt.mobile_number || bhakt.mobile || '').toLowerCase().includes(query) ||
            (bhakt.gotra || '').toLowerCase().includes(query) ||
            (bhakt.address || '').toLowerCase().includes(query) ||
            (Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types.join(', ') : bhakt.abhishek_types).toLowerCase().includes(query) ||
            relevantDates.some(date => date.abhishek_type.toLowerCase().includes(query));
        if (!match && query) return;

        html += `
            <div class="bhakt-section" style="margin-bottom: 2rem; padding: 1rem; border: 1px solid var(--border); border-radius: var(--radius);">
                <h4>${bhakt.name} (${bhakt.mobile_number || bhakt.mobile})</h4>
                <p><strong>Subscribed to:</strong> ${Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types.join(', ') : bhakt.abhishek_types}</p>
                <p><strong>Valid until:</strong> ${this.formatDate(bhakt.expiration_date)}</p>
                <p><strong>Upcoming Sacred Dates:</strong></p>
                <ul>
        `;
        relevantDates
            .filter(date => new Date(date.date) >= new Date())
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .slice(0, 5)
            .forEach(date => {
                html += `<li>${date.abhishek_type} - ${this.formatDate(date.date)}</li>`;
            });
        html += '</ul></div>';
    });

    html += '</div>';
    document.getElementById('combined-content').innerHTML = html;
}

    populateYearSelector() {
        const yearSelect = document.getElementById('schedule-year');
        const currentYear = new Date().getFullYear();
        for (let year = currentYear - 1; year <= currentYear + 2; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            if (year === currentYear) option.selected = true;
            yearSelect.appendChild(option);
        }
    }

    populateAbhishekTypeFilter() {
    // Fetch all Abhishek types from backend
    fetch('/abhishek_types')
        .then(res => res.json())
        .then(types => {
            const select = document.getElementById('abhishek-type-filter');
            if (select) {
                select.innerHTML = '<option value="">Select Abhishek Type</option>' +
                    types.map(type => `<option value="${type}">${type}</option>`).join('');
            }
        })
        .catch(err => console.error('Error fetching abhishek types:', err));
}

    setDefaultDate() {
        const now = new Date();
        const startDateInput = document.getElementById('start-date');
        if (startDateInput) startDateInput.value = now.toISOString().split('T')[0];
        const monthInput = document.getElementById('schedule-month');
        if (monthInput) monthInput.value = now.getMonth() + 1;
    }

    generateSchedule() {
    const month = parseInt(document.getElementById('schedule-month').value);
    const year = parseInt(document.getElementById('schedule-year').value);

    const scheduleContent = document.getElementById('schedule-content');
    scheduleContent.innerHTML = '<div class="loading"><div class="spinner"></div> Generating schedule...</div>';

    setTimeout(() => {
        const schedule = this.createMonthlySchedule(month, year);
        scheduleContent.innerHTML = schedule;
        this.populateAbhishekTypeFilter(); // <-- now uses all types
    }, 500);
}


    createMonthlySchedule(month, year) {
        const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'];

        const daysInMonth = new Date(year, month, 0).getDate();
        const monthSacredDates = this.sacredDates.filter(date => {
            const d = new Date(date.date);
            return d.getMonth() + 1 === month && d.getFullYear() === year;
        });

        let html = `<h3>${monthNames[month]} ${year} Schedule</h3>`;

        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            const dayEvents = monthSacredDates.filter(date => date.date === dateStr);

            if (dayEvents.length > 0) {
                html += `
                    <div class="schedule-day">
                        <div class="schedule-date">${this.formatDate(dateStr)} - ${this.getDayOfWeek(dateStr)}</div>
                        <div class="schedule-events">
                `;
                dayEvents.forEach(event => {
                    const participants = this.bhakts.filter(bhakt =>
                        (Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types : bhakt.abhishek_types.split(',')).includes(event.abhishek_type) &&
                        new Date(bhakt.expiration_date) >= new Date(dateStr)
                    );
                    html += `
                        <div class="schedule-event">
                            <strong>${event.abhishek_type}</strong> - ${participants.length} participants
                            ${participants.length > 0 ? `<br><small>${participants.map(p => p.name).join(', ')}</small>` : ''}
                        </div>
                    `;
                });
                html += '</div></div>';
            }
        }

        if (monthSacredDates.length === 0) {
            html += '<p>No sacred dates found for this month.</p>';
        }

        return html;
    }
    
    exportCSV() {
    const abhishekType = document.getElementById('abhishek-type-filter').value;

    if (!abhishekType) {
        alert('Please select an Abhishek Type.');
        return;
    }

    let csv = 'Participants,Abhishek Type\n';

    // Filter all Bhakts who have this Abhishek type
    const participants = this.bhakts.filter(b => 
        (Array.isArray(b.abhishek_types) ? b.abhishek_types : b.abhishek_types.split(',')).includes(abhishekType)
    );

    participants.forEach(bhakt => {
        csv += `"${bhakt.name}","${abhishekType}"\n`;
    });

    this.downloadFile(csv, `schedule-${abhishekType}.csv`, 'text/csv');
}



    exportHTML() {
    const month = parseInt(document.getElementById('schedule-month').value);
    const year = parseInt(document.getElementById('schedule-year').value);
    const abhishekType = document.getElementById('abhishek-type-filter').value;

    if (!abhishekType) {
        alert('Please select an Abhishek Type.');
        return;
    }

    // Backend route should filter Bhakts by month, year, and Abhishek type
    window.open(`/export/monthly_schedule_html?month=${month}&year=${year}&abhishek_type=${encodeURIComponent(abhishekType)}`, '_blank');
}


    downloadFile(content, filename, type) {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    loadCombinedView() {
        const combinedContent = document.getElementById('combined-content');
        let html = '<div class="combined-section">';
        html += '<h3>Active Bhakts and Their Sacred Dates</h3>';

        const activeBhakts = this.bhakts.filter(bhakt =>
            new Date(bhakt.expiration_date) > new Date()
        );

        activeBhakts.forEach(bhakt => {
            const relevantDates = this.sacredDates.filter(date =>
                (Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types : bhakt.abhishek_types.split(',')).includes(date.abhishek_type)
            );
            html += `
                <div class="bhakt-section" style="margin-bottom: 2rem; padding: 1rem; border: 1px solid var(--border); border-radius: var(--radius);">
                    <h4>${bhakt.name} (${bhakt.mobile_number || bhakt.mobile})</h4>
                    <p><strong>Subscribed to:</strong> ${Array.isArray(bhakt.abhishek_types) ? bhakt.abhishek_types.join(', ') : bhakt.abhishek_types}</p>
                    <p><strong>Valid until:</strong> ${this.formatDate(bhakt.expiration_date)}</p>
                    <p><strong>Upcoming Sacred Dates:</strong></p>
                    <ul>
            `;
            relevantDates
                .filter(date => new Date(date.date) >= new Date())
                .sort((a, b) => new Date(a.date) - new Date(b.date))
                .slice(0, 5)
                .forEach(date => {
                    html += `<li>${date.abhishek_type} - ${this.formatDate(date.date)}</li>`;
                });
            html += '</ul></div>';
        });

        html += '</div>';
        combinedContent.innerHTML = html;
    }

    // Generate labels based on selected Abhishek Type
   async generateLabels() {
    const selectedType = document.querySelector('#abhishek-type-filter').value;
    const includeMobile = document.querySelector('#include-mobile').checked;

    if (!selectedType) {
        alert('Please select an Abhishek type for labels.');
        return;
    }

    const labelsData = this.bhakts.filter(bhakt => 
        bhakt.abhishek_types.includes(selectedType) &&
        new Date(bhakt.expiration_date) >= new Date()
    );

    if (labelsData.length === 0) {
        alert('No active bhakts found for this type.');
        return;
    }

    // Find or create the container on the page
    let labelContainer = document.getElementById('label-print-container');
    if (!labelContainer) {
        labelContainer = document.createElement('div');
        labelContainer.id = 'label-print-container';
        labelContainer.style.display = 'flex';
        labelContainer.style.flexWrap = 'wrap';
        labelContainer.style.gap = '10px';
        labelContainer.style.padding = '10px';
        document.body.appendChild(labelContainer); // or append to a specific div on your page
    }

    // Clear previous labels
    labelContainer.innerHTML = '';

    // Generate new labels
    labelsData.forEach(bhakt => {
    const labelDiv = document.createElement('div');
    labelDiv.style.border = '1px solid #000';
    labelDiv.style.padding = '8px';
    labelDiv.style.width = '220px';
    labelDiv.style.minHeight = '90px';
    labelDiv.style.boxSizing = 'border-box';
    labelDiv.style.display = 'flex';
    labelDiv.style.flexDirection = 'column';
    labelDiv.style.justifyContent = 'center';
    labelDiv.style.alignItems = 'flex-start';
    labelDiv.style.fontSize = '13px';
    labelDiv.style.wordBreak = 'break-word';
    labelDiv.style.whiteSpace = 'normal';
    labelDiv.style.margin = '2px';

    // Function to create a row
    const createRow = (label, value) => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.gap = '4px'; // small space between label and value
        row.innerHTML = `<strong>${label}:</strong><span>${value || ''}</span>`;
        return row;
    };

    labelDiv.appendChild(createRow('Name', bhakt.name));
    labelDiv.appendChild(createRow('Address', bhakt.address));
    if (includeMobile) {
        labelDiv.appendChild(createRow('Mobile', bhakt.mobile_number));
    }

    labelContainer.appendChild(labelDiv);
});


}
    // Export labels to PDF
// Export labels to PDF with dynamic height
// Export labels to PDF with same logic as generateLabels
exportLabelsToPDF() {
    if (!window.jspdf) {
        alert('jsPDF library is not loaded!');
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const abhishekType = document.getElementById('abhishek-type-filter')?.value;
    const includeMobile = document.getElementById('include-mobile')?.checked;

    if (!abhishekType) {
        alert('Please select an Abhishek type.');
        return;
    }

    const labels = this.bhakts.filter(b => 
        b.abhishek_types.includes(abhishekType) &&
        new Date(b.expiration_date) >= new Date()
    );

    if (labels.length === 0) {
        alert('No active bhakts found for this type.');
        return;
    }

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 10;
    const spacing = 10;
    const labelWidth = (pageWidth - 2 * margin - spacing) / 2;

    let x = margin;
    let y = 10;

    for (let i = 0; i < labels.length; i += 2) {
        let pair = labels.slice(i, i + 2);

        let heights = [];
        let linesList = [];

        // prepare text for each label in the row
        pair.forEach(b => {
            const maxTextWidth = labelWidth - 6;
            let lines = [];

            lines.push(...doc.splitTextToSize(`Name: ${b.name || 'N/A'}`, maxTextWidth));
            lines.push(...doc.splitTextToSize(`Address: ${b.address || 'N/A'}`, maxTextWidth));

            // ✅ mobile added only if checkbox is checked
            if (includeMobile) {
                lines.push(...doc.splitTextToSize(`Mobile: ${b.mobile_number || b.mobile || 'N/A'}`, maxTextWidth));
            }

            const lineHeight = 6;
            const labelHeight = lines.length * lineHeight + 6;

            linesList.push(lines);
            heights.push(labelHeight);
        });

        // tallest label height for row alignment
        const rowHeight = Math.max(...heights);

        // draw each label in the row
        pair.forEach((b, index) => {
            const lines = linesList[index];
            const labelX = index === 0 ? x : x + labelWidth + spacing;

            doc.rect(labelX, y, labelWidth, rowHeight);

            let textY = y + 6;
            lines.forEach(line => {
                doc.text(line, labelX + 3, textY);
                textY += 6;
            });
        });

        // move down for next row
        y += rowHeight + 5;

        // new page if needed
        if (y + rowHeight > pageHeight - margin) {
            doc.addPage();
            y = 10;
        }
    }

    doc.save(`labels-${abhishekType}.pdf`);
    console.log(`PDF downloaded with ${labels.length} labels.`);
}



    // Call this in constructor or init
setupLabelEvents() {
    const generateBtn = document.getElementById('generate-labels-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', () => this.generateLabels());
    }

    const exportBtn = document.getElementById('export-labels-pdf');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => this.exportLabelsToPDF());
    }

    const mobileCheckbox = document.getElementById('print-mobile-checkbox');
    if (mobileCheckbox) {
        mobileCheckbox.addEventListener('change', () => this.generateLabels());
    }

    const addressCheckbox = document.getElementById('print-address-checkbox');
    if (addressCheckbox) {
        addressCheckbox.addEventListener('change', () => this.generateLabels());
    }
}


    formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    getDayOfWeek(dateStr) {
        return new Date(dateStr).toLocaleDateString('en-IN', { weekday: 'long' });
    }
}

// Initialize the system
window.bhaktSystem = new BhaktManagementSystem();