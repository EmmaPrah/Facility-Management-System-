document.addEventListener('DOMContentLoaded', function() {
    // Handle form submissions
    function submitForm(formId) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        
        fetch('/api/facilities', {
            method: formId.includes('edit') ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'An error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request');
        });
    }

    // Handle delete confirmation
    function confirmDelete(facilityId) {
        if (confirm('Are you sure you want to delete this facility?')) {
            fetch(`/api/facilities/${facilityId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message || 'An error occurred');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your request');
            });
        }
    }

    // Filter facilities by status
    function filterStatus(status) {
        const rows = document.querySelectorAll('.facility-row');
        rows.forEach(row => {
            if (status === 'All' || row.dataset.status === status) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Submit maintenance request
    function submitMaintenanceRequest() {
        const form = document.getElementById('maintenanceForm');
        const formData = new FormData(form);
        
        fetch('/api/maintenance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Maintenance request submitted successfully');
                form.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById('maintenanceModal'));
                modal.hide();
            } else {
                alert(data.message || 'An error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request');
        });
    }

    // View all activities
    function viewAllActivities() {
        // This would typically make an API call to get all activities
        // For now, we'll just show an alert
        alert('Viewing all activities is not yet implemented');
    }

    // Add event listeners for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const bsModal = new bootstrap.Modal(modal);
        modal.addEventListener('show.bs.modal', function (event) {
            // Reset form when modal is shown
            const form = this.querySelector('form');
            if (form) {
                form.reset();
            }
        });
    });
});
