// =======  Compute the median of a numeric array =======
function getMedian(arr) {
    const mid = Math.floor(arr.length / 2); // Calculate the middle index of the array
    return arr.length % 2 === 0
        ? (arr[mid - 1] + arr[mid]) / 2
        : arr[mid];
}

// ======= Convert hue + lightness to HSL color string =======
function getColor(hue, lightness = 92) {
    return `hsl(${hue}, 80%, ${lightness}%)`;
}

// ======= Draw the heatmap legend above the table =======
function drawHeatmapLegend(lowHue, topHue) {
    const canvas = document.getElementById('gradientHeatmap');
    const ctx = canvas.getContext('2d');

    const width = canvas.width;
    const height = canvas.height;

    const gradient = ctx.createLinearGradient(0, 0, width, 0);

    // Create 3-part gradient: Smallest (lowHue), Median (white), Largest (topHue)
    gradient.addColorStop(0, getColor(lowHue, 55));  // Smallest
    gradient.addColorStop(0.5, 'hsl(0, 0%, 100%)');  // Median = white
    gradient.addColorStop(1, getColor(topHue, 55));  // Largest

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
}

// ======= Apply background color to cells based on stats =======
function heatMapOneRow(cells, values, direction = 'more_is_better') {
    // Skip if too few values or all are the same (no variation to color)
    if (values.length < 2 || new Set(values).size === 1) return;

    // Sort values and calculate statistical parameters
    const sorted = [...values].sort((a, b) => a - b);
    const median = getMedian(sorted);
    const q1 = sorted[Math.floor((sorted.length - 1) / 4)];
    const q3 = sorted[Math.floor((sorted.length - 1) * 3 / 4)];
    const iqr = q3 - q1;

    // Calculate "fences" for mild/extreme outliers
    const lowOuter = q1 - 3 * iqr;
    const lowInner = q1 - 1.5 * iqr;
    const topInner = q3 + 1.5 * iqr;
    const topOuter = q3 + 3 * iqr;

    // Set up the color settings (hues/brightness)
    const YELLOW = 60, PURPLE = 280;
    const MID_BRT = 100, MIN_BRT = 75, INNER_BRT = 65, OUTER_BRT = 55;

    // Select hue direction depending on the metric
    const [lowHue, topHue] = direction === 'less_is_better' ? [PURPLE, YELLOW] : [YELLOW, PURPLE];

    // Apply coloring logic per cell
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        const num = values[i];
        let hue, lightness;

        if (num < lowOuter) {
            // Extreme low outlier
            hue = lowHue; lightness = OUTER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
            cell.style.color = 'white'; // improve contrast
        } else if (num < lowInner) {
            // Mid low outlier
            hue = lowHue; lightness = INNER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num < median) {
            // Between low inner and median → interpolate brightness
            hue = lowHue;
            const k = (MID_BRT - MIN_BRT) / (median - lowInner);
            lightness = MID_BRT - (median - num) * k;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num > topOuter) {
            // Extreme high outlier
            hue = topHue; lightness = OUTER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
            cell.style.color = 'white';
        } else if (num > topInner) {
            // Mild high outlier
            hue = topHue; lightness = INNER_BRT;
            cell.style.backgroundColor = getColor(hue, lightness);
        } else if (num > median) {
            // Between median and top inner → interpolate brightness
            hue = topHue;
            const k = (MID_BRT - MIN_BRT) / (topInner - median);
            lightness = MID_BRT - (num - median) * k;
            cell.style.backgroundColor = getColor(hue, lightness);
        }
        // If num === median → no color applied (keeps white)
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

        // Hide extended rows by default (only show "total" by default)
        const label = String(rowData[0] ?? '').toLowerCase();
        const isTotal = label.includes('(total)');
        const isMiningTool = label === 'mining_tool';
        const isCompTotal =
            label === '# bgcs (complete)' ||
            label === '# bgcs (incomplete)' ||
            label === 'mean bgc length (complete)' ||
            label === 'mean bgc length (incomplete)';
        if (!isTotal && !isMiningTool && !isCompTotal) {
            row.classList.add('extended-row');
        }


        const numericCells = [];
        const numericValues = [];

        // Build each cell in the row
        data[i].forEach((cell, j) => {
            const td = document.createElement(j === 0 ? 'th' : 'td');
            td.textContent = (j === 0 && String(cell).toLowerCase() === 'mining_tool')
                ? 'Genome Mining Tool'
                : cell;

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
// --- product colors (modifiable) ---
const productColors = {
    'NRP': '#2e8b57',
    'PKS': '#f4a460',
    'RiPP': '#4169e1',
    'Hybrid': '#b0c4de',
    'Terpene': '#800080',
    'Other': '#c7c2c1'
};

// Lighten a hex color toward white by "factor" (0..1)
function lighten(hex, factor = 0.5) {
    const num = parseInt(hex.slice(1), 16);
    let r = (num >> 16) & 0xff;
    let g = (num >> 8) & 0xff;
    let b = num & 0xff;
    r = Math.round(r + (255 - r) * factor);
    g = Math.round(g + (255 - g) * factor);
    b = Math.round(b + (255 - b) * factor);
    return `rgb(${r}, ${g}, ${b})`;
}

// Build the product checkboxes from data (NRP/PKS/RiPP/...)
function renderTypeFilters(types) {
    const group = document.getElementById('typeFilterGroup');
    if (!group) return;

    // Preserve the legend if present
    const legend = group.querySelector('legend');
    group.innerHTML = '';
    if (legend) group.appendChild(legend);

    const frag = document.createDocumentFragment();
    types.forEach(type => {
        const id = `type_${type.replace(/\W+/g, '_')}`;
        const label = document.createElement('label');
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.id = id;
        input.dataset.type = type;
        input.checked = true; // default: include
        label.appendChild(input);
        label.append(` ${type}`);
        frag.appendChild(label);
    });
    group.appendChild(frag);
}

// Which product checkboxes are ON
function selectedTypesFromUI(allTypes) {
    return allTypes.filter(t => {
        const el = document.getElementById(`type_${t.replace(/\W+/g, '_')}`);
        return !el || el.checked; // include if missing or checked
    });
}

// Which completeness statuses are ON
function selectedStatusesFromUI() {
  const on = [];
  if (document.getElementById('status_complete')?.checked)   on.push('complete');
  if (document.getElementById('status_incomplete')?.checked) on.push('incomplete');
  // If none selected, return empty array (chart will show nothing for completeness parts)
  return on;
}

// Enable/disable controls depending on mode
function syncShowByDisabled() {
    const isTotal   = document.getElementById('barModeTotal').checked;
    const showBy    = document.getElementById('barModeShowBy').checked;
    const byTypeOn  = document.getElementById('byType').checked;
    const byCompOn  = document.getElementById('byCompleteness').checked;

    const showByGroup = document.getElementById('showByGroup');
    if (showByGroup) showByGroup.disabled = isTotal;

    const typeFilterGroup = document.getElementById('typeFilterGroup');
    if (typeFilterGroup) typeFilterGroup.disabled = isTotal || !showBy || !byTypeOn;

    const completenessFilterGroup = document.getElementById('completenessFilterGroup');
    if (completenessFilterGroup) completenessFilterGroup.disabled = isTotal || !showBy || !byCompOn;
}


let bgcChart = null; // keep a reference so we can update/destroy cleanly

// --- Read data rows by label ---
function getRowByLabel(data, label) {
    return data.find(r => r[0] === label) || null;
}

// Return all product types that exist in the table (excluding 'total')
function detectTypes(data) {
    // matches: "# BGC (<Type>)"
    const types = new Set();
    for (const r of data) {
        const m = /^#\s*(?:complete|incomplete\s+)?BGC\s*\((.+)\)\s*$/i.exec(r[0]);
        if (m) {
            const type = m[1].trim();
            if (type.toLowerCase() !== 'total') types.add(type);
        }
    }
    // Product types
    const preferred = ['NRP', 'PKS', 'RiPP', 'Hybrid', 'Terpene'];
    const detected = Array.from(types);
    const ordered = [
        ...preferred.filter(t => detected.includes(t)),
        ...detected.filter(t => !preferred.includes(t))
    ];
    return ordered.length ? ordered : ['Other'];
}

function buildBarPlotDynamic(data) {
    // labels are Assembly+Tool as before
    const tools = data[1].slice(1);
    const assemblies = data[0].slice(1);
    const labels = tools.map((tool, i) => `${tool}\n${assemblies[i]}`);

    // read UI
    const mode = document.getElementById('barModeShowBy').checked ? 'showby' : 'total';
    const byCompleteness = document.getElementById('byCompleteness').checked;
    const byType = document.getElementById('byType').checked;

    let datasets = [];

    if (mode === 'total') {
        const row = getRowByLabel(data, '# BGC (total)');
        if (row) {
            const counts = row.slice(1).map(v => parseInt(v, 10));
            datasets.push({
                label: '# BGC (total)',
                data: counts,
                backgroundColor: '#322b7a'
            });
        }
    } else {
        // SHOW BY...
        if (byCompleteness && byType) {
            // stacks are (type x completeness)
            const allTypes = detectTypes(data);
            const types = selectedTypesFromUI(allTypes);
            const statuses = selectedStatusesFromUI();

            for (const type of types) {
                const baseColor = productColors[type] || productColors['Other'];
                const rowComplete = getRowByLabel(data, `# complete BGC (${type})`);
                const rowIncomplete = getRowByLabel(data, `# incomplete BGC (${type})`);

                if (statuses.includes('complete') && rowComplete) {
                    datasets.push({
                        label: `${type} complete`,
                        data: rowComplete.slice(1).map(v => parseInt(v, 10)),
                        backgroundColor: baseColor
                    });
                }
                if (statuses.includes('incomplete') && rowIncomplete) {
                    datasets.push({
                        label: `${type} incomplete`,
                        data: rowIncomplete.slice(1).map(v => parseInt(v, 10)),
                        backgroundColor: lighten(baseColor, 0.45) // lighter shade
                    });
                }
            }
        } else if (byCompleteness) {
            // stacks are complete vs incomplete (total)
            const rowComplete = getRowByLabel(data, '# complete BGC (total)');
            const rowIncomplete = getRowByLabel(data, '# incomplete BGC (total)');
            const statuses = selectedStatusesFromUI();

            if (statuses.includes('complete') && rowComplete) {
                datasets.push({
                    label: 'Complete',
                    data: rowComplete.slice(1).map(v => parseInt(v, 10)),
                    backgroundColor: '#578c18'
                });
            }
            if (statuses.includes('incomplete') && rowIncomplete) {
                datasets.push({
                    label: 'Incomplete',
                    data: rowIncomplete.slice(1).map(v => parseInt(v, 10)),
                    backgroundColor: '#ccca3d'
                });
            }
        } else if (byType) {
            // stacks are by type (totals per type)
            const allTypes = detectTypes(data);
            const types = selectedTypesFromUI(allTypes);
            for (const type of types) {
                const row = getRowByLabel(data, `# BGC (${type})`);
                if (row) {
                    datasets.push({
                        label: type,
                        data: row.slice(1).map(v => parseInt(v, 10)),
                        backgroundColor: productColors[type] || productColors['Other']
                    });
                }
            }
        } else {
            // fallback: if user selected "Show by" but no boxes,
            // just show the total to avoid an empty chart.
            const row = getRowByLabel(data, '# BGC (total)');
            if (row) {
                const counts = row.slice(1).map(v => parseInt(v, 10));
                datasets.push({
                    label: '# BGC (total)',
                    data: counts,
                    backgroundColor: '#322b7a'
                });
            }
        }
    }

    // cleanup previous chart
    if (bgcChart) {
        bgcChart.destroy();  // clean up the old chart instance
        bgcChart = null;
    }

    // stacked if more than one dataset
    const stacked = datasets.length > 1;

    bgcChart = new Chart(document.getElementById('bgcBarPlot'), { // save the new chart in the same variable
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true, // height auto-adjusts from width
            aspectRatio: 1.7,          // tweak: width / height (e.g., 1.6, 1.7, 1.8)
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.raw}`
                    }
                }
            },
            scales: {
                x: { stacked },
                y: { beginAtZero: true, stacked }
            }
        }
    });
}


// ======= Setup on Page Load =======
document.addEventListener('DOMContentLoaded', () => {
    buildTable(reportData);
    renderTypeFilters(detectTypes(reportData));
    buildBarPlotDynamic(reportData);

    // Toggle visibility of extended report rows
    const toggleBtn = document.getElementById('toggleExtendedBtn');
    toggleBtn.addEventListener('click', () => {
        const extendedRows = document.querySelectorAll('.extended-row');
        if (!extendedRows.length) return; // nothing to toggle
        const isHidden = getComputedStyle(extendedRows[0]).display === 'none';

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

    // Bar plot controls listeners ===
    // Radios & "by ..." checkboxes: sync disabled state + rebuild
    ['barModeTotal','barModeShowBy','byCompleteness','byType'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => {
            syncShowByDisabled();
            buildBarPlotDynamic(reportData);
        });
    });

    // Delegate product checkbox changes to the fieldset
    const typeGroup = document.getElementById('typeFilterGroup');
    if (typeGroup) {
        typeGroup.addEventListener('change', (e) => {
            if (e.target && e.target.matches('input[type="checkbox"]')) {
                buildBarPlotDynamic(reportData);
            }
        });
    }

    // Add the event listener for complete/incomplete
    const compGroup = document.getElementById('completenessFilterGroup');
    if (compGroup) {
        compGroup.addEventListener('change', (e) => {
            if (e.target && e.target.matches('input[type="checkbox"]')) {
                buildBarPlotDynamic(reportData);
            }
        });
    }

    // Initialize disabled/enabled state on first load
    syncShowByDisabled();

    // document.getElementById('barModeTotal').addEventListener('change', syncShowByDisabled);
    // document.getElementById('barModeShowBy').addEventListener('change', syncShowByDisabled);
    // syncShowByDisabled();
    // // Re-render when the Show by checkboxes change
    // ['byCompleteness','byType'].forEach(id => {
    //     const el = document.getElementById(id);
    //     if (el) el.addEventListener('change', () => buildBarPlotDynamic(reportData));
    // });

    // Draw heatmap gradient
    drawHeatmapLegend(60, 280);  // yellow to purple


});
