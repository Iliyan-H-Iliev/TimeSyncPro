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
