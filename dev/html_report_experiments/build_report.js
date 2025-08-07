// ======= Helper Function: Get Median =======
function getMedian(arr) {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0
        ? (sorted[mid - 1] + sorted[mid]) / 2
        : sorted[mid];
}

// ======= Helper Function: Convert hue + lightness to HSL color string =======
function getColor(hue, lightness = 92) {
    return `hsl(${hue}, 80%, ${lightness}%)`;
}

function drawHeatmapLegend(lowHue, topHue) {
    const canvas = document.getElementById('gradientHeatmap');
    const ctx = canvas.getContext('2d');

    const width = canvas.width;
    const height = canvas.height;

    const gradient = ctx.createLinearGradient(0, 0, width, 0);

    // Create 3-part gradient: Worst (lowHue), Median (white), Best (topHue)
    gradient.addColorStop(0, getColor(lowHue, 55));  // Worst
    gradient.addColorStop(0.5, 'hsl(0, 0%, 100%)');  // Median = white
    gradient.addColorStop(1, getColor(topHue, 55));  // Best

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
}

// ======= Main Heatmap Function: Apply background color to cells based on stats =======
function heatMapOneRow(cells, values, direction = 'more_is_better') {
    if (values.length < 2 || new Set(values).size === 1) return;

    // Step 1: Calculate statistical parameters
    const sorted = [...values].sort((a, b) => a - b);
    const median = getMedian(sorted);
    const q1 = sorted[Math.floor((sorted.length - 1) / 4)];
    const q3 = sorted[Math.floor((sorted.length - 1) * 3 / 4)];
    const iqr = q3 - q1;

    // Step 2: Calculate "fences" for mild/extreme outliers
    const lowOuter = q1 - 3 * iqr;
    const lowInner = q1 - 1.5 * iqr;
    const topInner = q3 + 1.5 * iqr;
    const topOuter = q3 + 3 * iqr;

    // Step 3: Color settings
    const YELLOW = 60, PURPLE = 280;
    const MID_BRT = 100, MIN_BRT = 75, INNER_BRT = 65, OUTER_BRT = 55;

    // Step 4: Select hue direction depending on the metric
    const [lowHue, topHue] = direction === 'less_is_better' ? [PURPLE, YELLOW] : [YELLOW, PURPLE];

    // Step 5: Apply coloring logic per cell
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        const num = values[i];
        let hue, lightness;

        if (num < lowOuter) {
            hue = lowHue; lightness = OUTER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
            cell.style.color = 'white'; // improve contrast
        } else if (num < lowInner) {
            hue = lowHue; lightness = INNER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num < median) {
            hue = lowHue;
            const k = (MID_BRT - MIN_BRT) / (median - lowInner);
            lightness = MID_BRT - (median - num) * k;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num > topOuter) {
            hue = topHue; lightness = OUTER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
            cell.style.color = 'white';
        } else if (num > topInner) {
            hue = topHue; lightness = INNER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num > median) {
            hue = topHue;
            const k = (MID_BRT - MIN_BRT) / (topInner - median);
            lightness = MID_BRT - (num - median) * k;
            cell.style.backgroundColor = getColor(hue, lightness);
        }
    }
}

const allNumericCells = [];
// ======= Table Builder =======
function buildTable(data) {
    allNumericCells.length = 0;
    const container = document.getElementById('reportTableContainer');
    const table = document.createElement('table');
    const headerRow = document.createElement('tr');

    // Build column headers
    headerRow.appendChild(document.createElement('th')); // top-left empty cell
    data[0].slice(1).forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Loop over each data row
    for (let i = 1; i < data.length; i++) {
        const row = document.createElement('tr');
        const rowData = data[i];

        // Hide extended rows by default (toggle later)
        if (i > 6) row.classList.add('extended-row');

        const numericCells = [];
        const numericValues = [];

        // Build each cell in the row
        data[i].forEach((cell, j) => {
            const td = document.createElement(j === 0 ? 'th' : 'td');
            td.textContent = cell;

            // Only collect numeric values for heatmap
            if (j > 0) {
                const num = parseFloat(cell);
                if (!isNaN(num)) {
                    numericCells.push(td);
                    numericValues.push(num);
                }
            }

            row.appendChild(td);
        });

        // Apply the statistical heatmap coloring
        heatMapOneRow(numericCells, numericValues);
        allNumericCells.push({ cells: numericCells, values: numericValues });

        table.appendChild(row);
    }

    container.appendChild(table);
}

// ======= Bar Chart Builder =======
function buildBarPlot(data) {
    const row = data.find(r => r[0] === '# BGC (total)');
    if (!row) return;

    const tools = data[1].slice(1);
    const assemblies = data[0].slice(1);
    const labels = tools.map((tool, i) => `${tool}\n${assemblies[i]}`);
    const counts = row.slice(1).map(v => parseInt(v));

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

// ======= Setup on Page Load =======
document.addEventListener('DOMContentLoaded', () => {
    buildTable(reportData);
    buildBarPlot(reportData);

    // Toggle visibility of extended report rows
    const toggleBtn = document.getElementById('toggleExtendedBtn');
    toggleBtn.addEventListener('click', () => {
        const extendedRows = document.querySelectorAll('.extended-row');
        const isHidden = extendedRows[0]?.style.display === 'none';

        extendedRows.forEach(row => {
            row.style.display = isHidden ? 'table-row' : 'none';
        });

        toggleBtn.textContent = isHidden ? 'Hide Extended Report' : 'Show Extended Report';
    });

    const heatmapToggle = document.getElementById('heatmapToggle');
    heatmapToggle.addEventListener('change', () => {
        const show = heatmapToggle.checked;
        allNumericCells.forEach(({ cells, values }) => {
            if (show) {
                heatMapOneRow(cells, values);
            } else {
                cells.forEach(cell => {
                    cell.style.backgroundColor = '';
                    cell.style.color = '';
                });
            }
        });
    });
    // Draw heatmap gradient
    drawHeatmapLegend(60, 280);  // yellow to purple


});
