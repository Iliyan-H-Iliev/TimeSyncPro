function loadTeams(page = 1) {
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
