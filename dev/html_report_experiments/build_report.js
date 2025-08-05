function getHeatmapColor(value, min, max) {
    const num = parseFloat(value);
    if (isNaN(num)) return '';

    if (min === max) return '#c4c4c4'; // neutral color if no range

    const scale = chroma.scale('PRGn').domain([min, max]);
    // const baseColor = scale(num);
    // const color = baseColor.brighten(1).hex();
    return scale(num).hex(); // returns color HEX code
}

function buildBarPlot(data) {
    // Find the row with "# BGC (total)"
    const row = data.find(r => r[0] === '# BGC (total)');
    if (!row) return;

    // Labels = tool + assembly from first 2 rows
    const tools = data[1].slice(1);     // "Genome mining tool"
    const assemblies = data[0].slice(1); // "Genome mining file"
    const labels = tools.map((tool, i) => `${tool}\n${assemblies[i]}`);

    // Data = counts from the "# BGC (total)" row
    const counts = row.slice(1).map(v => parseInt(v));

    // Create the chart
    new Chart(document.getElementById('bgcBarPlot'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '# BGC (total)',
                data: counts,
                backgroundColor: '#6cae75'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `# BGCs: ${ctx.raw}`
                    }
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}



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
    }); // Loops through the first row of data (data[0]), skipping the first item (the row label)
    table.appendChild(headerRow);

    // Data rows + heatmap
    for (let i = 1; i < data.length; i++) {
        const row = document.createElement('tr');
        const rowData = data[i];

        // Mark extended rows
        if (i > 6) {
            row.classList.add('extended-row');
        }

        // Get numeric values for each row
        const numericValues = rowData.slice(1)
            .map(v => parseFloat(v))
            .filter(v => !isNaN(v));
        const min = Math.min(...numericValues);
        const max = Math.max(...numericValues); // Find the smallest and largest numbers in that row

        data[i].forEach((cell, j) => {
            const td = document.createElement(j === 0 ? 'th' : 'td');
            td.textContent = cell;

            //Apply heatmap to numeric cells
            if (j>0) {
                const color = getHeatmapColor(cell, min, max)
                if (color) {
                    td.style.backgroundColor = color;
                }
            }
            row.appendChild(td);
        });
        table.appendChild(row);
    }

    container.appendChild(table);
}

document.addEventListener('DOMContentLoaded', () => {
    buildTable(reportData);
    buildBarPlot(reportData);

    const toggleBtn = document.getElementById('toggleExtendedBtn');
    toggleBtn.addEventListener('click', () => {
        const extendedRows = document.querySelectorAll('.extended-row');
        const isHidden = extendedRows[0]?.style.display === 'none';

        extendedRows.forEach(row => {
            row.style.display = isHidden ? 'table-row' : 'none';
        });

        toggleBtn.textContent = isHidden ? 'Hide Extended Report' : 'Show Extended Report';
    });
});
