function loadEmployees(page = 1) {
    const employeesList = document.getElementById('employees-list');
    employeesList.innerHTML = '<div class="loading">Loading employees...</div>';

    fetch(`${apiConfig.urls.employees}?page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (!data.results || data.results.length === 0) {
                employeesList.innerHTML = '<div class="no-data">No employees found</div>';
                return;
            }

            employeesList.innerHTML = data.results.map(employee => `
                <div class="employee-row">
                    <div class="employee-info">
                        <div class="employee-name">Name: ${employee.first_name} ${employee.last_name}</div>
                        <div class="employee-details">
                            ${employee.role ? `<span class="badge bg-secondary">Role: ${employee.role}</span>` : ''}
                            ${employee.employee_id ? `<span class="badge bg-info">Employee ID: ${employee.employee_id}</span>` : ''}
                        </div>
                    </div>

                </div>
            `).join('');

            renderPagination(data, 'employees-pagination', loadEmployees);
        })
        .catch(error => {
            console.error('Error:', error);
            employeesList.innerHTML = '<div class="error">Error loading employees</div>';
        });
}
