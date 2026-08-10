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


function filterTable() {
    tableRows.forEach(row => {
        const cells = row.querySelectorAll('td');

        const matchesAllFilters = columnFilters.every(filter => {
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

        row.hidden = !matchesAllFilters;
    });
}


// Re-filter immediately whenever the user changes any search field.
columnFilters.forEach(filter => {
    filter.addEventListener('input', filterTable);
});