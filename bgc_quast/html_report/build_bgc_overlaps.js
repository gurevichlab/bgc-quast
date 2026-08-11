/*
 * Interactive column filtering for the overlapping-BGC table.
 *
 * Each filter input stores the index of the column it controls in its
 * data-column attribute. Filters are case-insensitive and are combined:
 * a row remains visible only if it matches every non-empty filter.
 */

const columnFilters = Array.from(
    document.querySelectorAll('.column-filter')
);

const tableRows = Array.from(
    document.querySelectorAll('.bgc-overlap-table tbody tr')
);

const rowsPerPageSelect = document.getElementById('rows-per-page');
const paginationInfo = document.getElementById('pagination-info');
const pageInfo = document.getElementById('page-info');
const previousPageButton = document.getElementById('previous-page');
const nextPageButton = document.getElementById('next-page');

let currentPage = 1;

/*
 * Return true when a table row satisfies every active column filter.
 */
function rowMatchesFilters(row) {
    const cells = row.querySelectorAll('td');

    return columnFilters.every(filter => {
        const query = filter.value.trim();

        // An empty filter does not restrict the table.
        if (query === '') {
            return true;
        }

        const columnIndex = Number(filter.dataset.column);
        const filterType = filter.dataset.filterType;
        const cellText = cells[columnIndex].textContent.trim();

        if (filterType === 'min') {
            return Number(cellText) >= Number(query);
        }

        if (filterType === 'max') {
            return Number(cellText) <= Number(query);
        }

        // Text filters are case-insensitive substring searches.
        return cellText.toLowerCase().includes(query.toLowerCase());
    });
}


/*
 * Apply active filters and display only the rows belonging to the
 * currently selected page.
 */
function updateTable() {
    const matchingRows = tableRows.filter(rowMatchesFilters);
    const rowsPerPage = Number(rowsPerPageSelect.value);
    const totalPages = Math.max(1, Math.ceil(matchingRows.length / rowsPerPage));

    // Keep the current page valid if filtering reduces the number of pages.
    currentPage = Math.min(currentPage, totalPages);

    const firstRowIndex = (currentPage - 1) * rowsPerPage;
    const lastRowIndex = firstRowIndex + rowsPerPage;
    const visibleRows = matchingRows.slice(firstRowIndex, lastRowIndex);

    // Hide all rows first, then reveal only the current page.
    tableRows.forEach(row => {
        row.hidden = true;
    });

    visibleRows.forEach(row => {
        row.hidden = false;
    });

    updatePagination(
        matchingRows.length,
        firstRowIndex,
        visibleRows.length,
        totalPages
    );
}


/*
 * Update pagination text and enable/disable navigation buttons.
 */
function updatePagination(
    matchingRowCount,
    firstRowIndex,
    visibleRowCount,
    totalPages
) {
    if (matchingRowCount === 0) {
        paginationInfo.textContent = 'Showing 0 of 0';
    } else {
        const firstDisplayedRow = firstRowIndex + 1;
        const lastDisplayedRow = firstRowIndex + visibleRowCount;

        paginationInfo.textContent =
            `Showing ${firstDisplayedRow}\u2013${lastDisplayedRow} of ${matchingRowCount}`;
    }

    pageInfo.textContent = `${currentPage} / ${totalPages}`;

    previousPageButton.disabled = currentPage === 1;
    nextPageButton.disabled = currentPage === totalPages;
}


// Re-filter immediately whenever the user changes any search field.
columnFilters.forEach(filter => {
    filter.addEventListener('input', () => {
        currentPage = 1;
        updateTable();
    });
});

// Changing the number of rows per page restarts pagination from page 1.
rowsPerPageSelect.addEventListener('change', () => {
    currentPage = 1;
    updateTable();
});


previousPageButton.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage -= 1;
        updateTable();
    }
});


nextPageButton.addEventListener('click', () => {
    currentPage += 1;
    updateTable();
});


// Initialize the table with the default page size.
updateTable();