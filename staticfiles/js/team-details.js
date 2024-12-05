document.addEventListener('DOMContentLoaded', function() {
   // Initial load
   loadEmployees();
   loadHistory();
    loadTeams();
});

// Employees handling
// const updateProfileUrl = "{% url 'update_profile' slug='PLACEHOLDER' %}";
function loadEmployees(page = 1) {
   // Add loading state
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
                   <div class="employee-actions">
                       <a href="${apiConfig.urls.updateProfile.replace('PLACEHOLDER', employee.user_slug)}?next=${encodeURIComponent(window.location.pathname)}" 
                               class="btn-icon" title="Edit">
                           <i class="fa-solid fa-pen-to-square"></i>
                       </a>
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

// History handling
function loadHistory(page = 1) {
   const historyList = document.getElementById('history-list');
   historyList.innerHTML = '<div class="loading">Loading history...</div>';

   fetch(`${apiConfig.urls.history}?page=${page}`)
       .then(response => {
           if (!response.ok) throw new Error('Network response was not ok');
           return response.json();
       })
       .then(data => {
           if (!data.results || data.results.length === 0) {
               historyList.innerHTML = '<div class="no-data">No history records found</div>';
               return;
           }

           historyList.innerHTML = data.results.map(record => `
               <div class="history-item">
                   <div class="history-header">
                       <span class="timestamp">
                           ${new Date(record.timestamp).toLocaleString()}
                       </span>
                       <span class="badge bg-${getActionBadgeClass(record.action)}">
                           ${record.action}
                       </span>
                       <span class="changed-by">by ${record.changed_by || 'System'}</span>
                   </div>
                   <div class="changes">
                       <strong>${record.change_summary}</strong>
                   </div>
               </div>
           `).join('');

           renderPagination(data, 'history-pagination', loadHistory);
       })
       .catch(error => {
           console.error('Error:', error);
           historyList.innerHTML = '<div class="error">Error loading history</div>';
       });
}


function loadTeams(page = 1) {
    console.log(apiConfig.urls.teams);
    // Add loading state
    const teamsList = document.getElementById('teams-list');
    teamsList.innerHTML = '<div class="loading">Loading teams...</div>';

    fetch(`${apiConfig.urls.teams}?page=${page}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (!data.results || data.results.length === 0) {
                teamsList.innerHTML = '<div class="no-data">No teams found</div>';
                return;
            }

            teamsList.innerHTML = data.results.map(team => `
                <div class="team-row">
                    <div class="team-info">
                        <div class="team-name">Team: ${team.name}</div>
                        <div class="team-details">
                            ${team.holiday_approver_name ? 
                                `<span class="badge bg-secondary">Holiday Approver: ${team.holiday_approver_name}</span>` : '<span class="badge bg-secondary">Holiday Approver: -</span>'}
                            ${team.department_name ? 
                                `<span class="badge bg-info">Department: ${team.department_name}</span>` : '<span class="badge bg-info">Department: -</span>'}
                            <span class="badge bg-primary">Members: ${team.employee_count || 0}</span>
                        </div>
                    </div>
                </div>
            `).join('');

            renderPagination(data, 'teams-pagination', loadTeams);
        })
        .catch(error => {
            console.error('Error:', error);
            teamsList.innerHTML = '<div class="error">Error loading teams</div>';
        });
}

// Helper functions
function renderPagination(data, elementId, loadFunction) {
   const paginationElement = document.getElementById(elementId);

   // Check if pagination is needed
   if (!data || data.count <= data.results.length) {
       paginationElement.innerHTML = '';
       return;
   }

   const currentPage = data.current_page || 1;  // Get current page from API response
   const totalPages = Math.ceil(data.count / data.page_size);

   let html = `<nav aria-label="Page navigation"><ul class="pagination justify-content-center">`;

   // Previous/First buttons - Only show if not on first page
   if (currentPage <= 1) {
       html += `
           <li class="page-item disabled">
               <span class="page-link">&laquo; First</span>
           </li>
           <li class="page-item disabled">
               <span class="page-link">Previous</span>
           </li>
       `;
   } else {
       html += `
           <li class="page-item">
               <a class="page-link" href="javascript:void(0)" data-page="1">&laquo; First</a>
           </li>
           <li class="page-item">
               <a class="page-link" href="javascript:void(0)" data-page="${currentPage - 1}">Previous</a>
           </li>
       `;
   }

   // Current page indicator
   html += `
       <li class="page-item active">
           <span class="page-link">Page ${currentPage} of ${totalPages}</span>
       </li>
   `;

   // Next/Last buttons - Only show if not on last page
   if (currentPage >= totalPages) {
       html += `
           <li class="page-item disabled">
               <span class="page-link">Next</span>
           </li>
           <li class="page-item disabled">
               <span class="page-link">Last &raquo;</span>
           </li>
       `;
   } else {
       html += `
           <li class="page-item">
               <a class="page-link" href="javascript:void(0)" data-page="${currentPage + 1}">Next</a>
           </li>
           <li class="page-item">
               <a class="page-link" href="javascript:void(0)" data-page="${totalPages}">Last &raquo;</a>
           </li>
       `;
   }

   html += `</ul></nav>`;
   paginationElement.innerHTML = html;

   // Add click handlers only to enabled links
   paginationElement.querySelectorAll('a.page-link').forEach(link => {
       link.addEventListener('click', (e) => {
           e.preventDefault();
           const page = parseInt(e.target.dataset.page);
           if (!isNaN(page)) {
               loadFunction(page);
           }
       });
   });
}

function getActionBadgeClass(action) {
   const classes = {
       'create': 'success',
       'update': 'primary',
       'delete': 'danger',
       'register': 'info'
   };
   return classes[action] || 'secondary';
}

function formatChanges(changes, record) {
   if (!changes) return 'No changes recorded';

   return Object.entries(changes)
       .map(([field, change]) => `
           <div class="change-item">
               <strong>${field.replaceAll('_', ' ').toUpperCase()}:</strong>
               <span>${record}</span>
               <span class="old-value">${change.old || 'None'}</span>
               <i class="fas fa-arrow-right"></i>
               <span class="new-value">${change.new || 'None'}</span>
           </div>
       `)
       .join('');
}