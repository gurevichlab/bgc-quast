function buildTable(data) {
    const container = document.getElementById('reportTableContainer');
    const table = document.createElement('table');
    const headerRow = document.createElement('tr');
    
    // Column headers (first row)
    headerRow.appendChild(document.createElement('th')); // top-left empty cell
    data[0].slice(1).forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    
    // Data rows
    for (let i = 1; i < data.length; i++) {
        const row = document.createElement('tr');
        data[i].forEach((cell, j) => {
            const td = document.createElement(j === 0 ? 'th' : 'td');
            td.textContent = cell;
            row.appendChild(td);
        });
        table.appendChild(row);
    }

    container.appendChild(table);
}

document.addEventListener('DOMContentLoaded', () => {
    buildTable(reportData);
});

