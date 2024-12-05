function renderPagination(data, elementId, loadFunction) {
    const paginationElement = document.getElementById(elementId);

    if (!data || data.count <= data.results.length) {
        paginationElement.innerHTML = '';
        return;
    }

    const currentPage = data.current_page || 1;
    const totalPages = Math.ceil(data.count / data.page_size);

    let html = `<nav aria-label="Page navigation"><ul class="pagination justify-content-center">`;

    if (currentPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" data-page="1">&laquo; First</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" data-page="${currentPage - 1}">Previous</a>
            </li>`;
    }

    html += `<li class="page-item active"><span class="page-link">Page ${currentPage} of ${totalPages}</span></li>`;

    if (currentPage < totalPages) {
        html += `
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" data-page="${currentPage + 1}">Next</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="javascript:void(0)" data-page="${totalPages}">Last &raquo;</a>
            </li>`;
    }

    html += `</ul></nav>`;
    paginationElement.innerHTML = html;

    paginationElement.querySelectorAll('a.page-link').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            if (!isNaN(page)) {
                loadFunction(page);
            }
        });
    });
}
