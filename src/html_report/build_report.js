/* ---------------------------------------------------------------------------
 * HEATMAP UTILITIES
 * ------------------------------------------------------------------------- */

/**
 * Compute the median of a sorted numeric array
 * @param {number[]} arr
 *  @returns {number}
 */
function getMedian(arr) {
    const mid = Math.floor(arr.length / 2); // Calculate the middle index of the array
    return arr.length % 2 === 0
        ? (arr[mid - 1] + arr[mid]) / 2
        : arr[mid];
}

/**
 * Convert hue + lightness to an HSL color string.
 * @param {number} hue
 * @param {number} [lightness=92]
 * @returns {string}
 */
function getColor(hue, lightness = 92) {
    return `hsl(${hue}, 80%, ${lightness}%)`;
}

/**
 * Draw the heatmap legend (smallest → median → largest) above the table.
 * @param {number} lowHue
 * @param {number} topHue
 */
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

/**
 * Apply background color to cells in a single row based on outliers/statistics.
 * @param {HTMLTableCellElement[]} cells
 * @param {number[]} values
 * @param {'more_is_better'|'less_is_better'} [direction='more_is_better']
 */
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

/**
 * Global store to re-apply/remove heatmap colors when toggling the heatmap.
 * Each entry: { cells: HTMLTableCellElement[], values: number[] }
 */
const allNumericCells = [];


/* ---------------------------------------------------------------------------
 * TABLE BUILDER (main report table + extended rows)
 * ------------------------------------------------------------------------- */
const isReferenceMode = (typeof reportMode !== 'undefined' && reportMode === "compare_to_reference");

/**
 * Build the main report table and insert it into #reportTableContainer.
 * @param {Array[]} data - 2D array representing the report pivot table.
 */
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
            label === '# bgcs (unknown completeness)' ||
            label === 'mean bgc length (complete)' ||
            label === 'mean bgc length (incomplete)' ||
            label === 'mean bgc length (unknown completeness)';
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
                    // Special handling for reference-column cells in Reference mode
                    const isLastCol = (j === rowData.length - 1);
                    const rowLabel = String(rowData[0] ?? '');
                    const isBGCRow = rowLabel.startsWith('# BGCs');
                    const isMeanRow = rowLabel.startsWith('Mean BGC length');

                    if (isReferenceMode && isLastCol) {
                        // Don't include the reference column value in numericCells/values (remove it from the heatmap)
                        // - For non-BGC/Mean rows, also hide the 0 and make the cell visually empty.
                        if (!isBGCRow && !isMeanRow) {
                            td.textContent = '';
                            td.classList.add('ref-empty');  // optional, for styling
                        }
                        // BGC / Mean rows keep their text, but are still excluded from heatmap.
                    } else {
                        // Normal data cell → use it for heatmap
                        numericCells.push(td);
                        numericValues.push(num);
                    }
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

/* ---------------------------------------------------------------------------
 * BAR CHART BUILDER (Chart.js) – totals / by type / by completeness
 * ------------------------------------------------------------------------- */

// --- product colors (modifiable) ---
const productColors = {
    'NRPS': '#2e8b57',
    'PKS': '#f4a460',
    'RiPP': '#4169e1',
    'Hybrid': '#b0c4de',
    'Terpene': '#800080',
    'Saccharide': '#f0c107',
    'Alkaloid': '#dda0dd',
    'Other': '#666666'
};

/**
 * Lighten a HEX color toward white by a factor in [0, 1].
 * @param {string} hex
 * @param {number} [factor=0.5]
 * @returns {string}
 */
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

/**
 * Build the dynamic product checkboxes (NRPS/PKS/RiPP/...) in #typeFilterGroup.
 * @param {string[]} types
 */
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

/**
 * Build the dynamic completeness checkboxes (Complete/Incomplete/Unknown completeness)
 * based only on what appears in the table.
 * @param {string[]} statuses
 */
function renderCompletenessFilters(statuses) {
    const group = document.getElementById('completenessFilterGroup');
    if (!group) return;

    // Preserve the <legend>
    const legend = group.querySelector('legend');
    group.innerHTML = '';
    if (legend) group.appendChild(legend);

    const frag = document.createDocumentFragment();
    statuses.forEach(status => {
        const id = 'status_' + status.replace(/\s+/g, '_');
        const label = document.createElement('label');
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.id = id;
        input.checked = true; // default ON
        label.appendChild(input);
        // Capitalize
        let niceLabel;
        if (status === 'unknown completeness') {
            niceLabel = 'Unknown completeness';
        } else {
            niceLabel = status.charAt(0).toUpperCase() + status.slice(1);
}
        label.append(` ${niceLabel}`);
        frag.appendChild(label);
    });

    group.appendChild(frag);
}

/**
 * Return which product types are currently selected in the UI.
 * Missing checkboxes default to "on".
 * @param {string[]} allTypes
 * @returns {string[]}
 */
function selectedTypesFromUI(allTypes) {
    return allTypes.filter(t => {
        const el = document.getElementById(`type_${t.replace(/\W+/g, '_')}`);
        return !el || el.checked; // include if missing or checked
    });
}

/**
 * Return completeness statuses that are currently selected in the UI.
 * @returns {('complete'|'incomplete'|'unknown completeness')[]}
 */
function selectedStatusesFromUI() {
  const on = [];
  if (document.getElementById('status_complete')?.checked)   on.push('complete');
  if (document.getElementById('status_incomplete')?.checked) on.push('incomplete');
  if (document.getElementById('status_unknown_completeness')?.checked) on.push('unknown completeness');
  // If none selected, return empty array (chart will show nothing for completeness parts)
  return on;
}

/**
 * Enable/disable controls depending on bar chart mode and "show by" choices.
 */
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

/** Keep an empty variable so we can update/destroy the chart cleanly. */
let bgcChart = null;

/**
 * Find a row in the data by its label (first column).
 * @param {Array[]} data
 * @param {string} label
 * @returns {Array|null}
 */
function getRowByLabel(data, label) {
    return data.find(r => r[0] === label) || null;
}

/**
 * Return all product types that exist in the table (excluding "total"/pure
 * completeness rows). Types are parsed from labels like "# BGCs (NRPS, Complete)".
 * @param {Array[]} data
 * @returns {string[]}
 */
function detectTypes(data) {
  const types = new Set();

  for (const r of data) {
    const s = String(r[0] ?? '');
    // Match labels that start with "# BGCs ( ... )"
    const m = /^#\s*BGCs?\s*\(\s*([^)]+)\s*\)\s*$/i.exec(s);
    if (!m) continue;

    // inside is: "NRPS" or "NRPS, Complete" or "Complete" etc.
    const inside = m[1].trim();

    // take only the part before the first comma (the product)
    const [typeRaw] = inside.split(',', 1);
    const type = (typeRaw || '').trim();
    if (!type) continue;

    // skip non-product tokens that appear as totals
    const lc = type.toLowerCase();
    if (lc === 'total' || lc === 'complete' || lc === 'incomplete' || lc === 'unknown completeness') continue;

    types.add(type);
  }

  // Preferred order + fallback to 'Other' if nothing detected
  const preferred = ['NRPS','PKS','RiPP','Terpene','Saccharide','Alkaloid','Hybrid'];
  const detected = Array.from(types);
  const ordered = [
    ...preferred.filter(t => detected.includes(t)),
    ...detected.filter(t => !preferred.includes(t))
  ];
  return ordered.length ? ordered : ['Other'];
}

/**
 * Detect which completeness statuses exist in the table.
 * Looks for rows like "# BGCs (Complete)" or "# BGCs (Type, Unknown completeness)".
 * @param {Array[]} data
 * @returns {string[]}
 */
function detectCompleteness(data) {
    const allowed = ['complete', 'incomplete', 'unknown completeness'];
    const set = new Set();

    data.forEach(row => {
        const label = String(row[0] || '').trim();

        // total rows, e.g. "# BGCs (Unknown completeness)"
        let m = /^#\s*BGCs\s*\(\s*([^)]+)\s*\)$/i.exec(label);
        if (m) {
            const inside = m[1]
                .split(',')
                .map(s => s.trim().toLowerCase());

            inside.forEach(v => {
                if (allowed.includes(v)) {
                    set.add(v);
                }
            });
        }

        // typed rows, e.g. "# BGCs (NRPS, Unknown completeness)"
        m = /^#\s*BGCs\s*\(\s*([^,]+),\s*([^)]+)\)$/i.exec(label);
        if (m) {
            const status = m[2].trim().toLowerCase();
            if (allowed.includes(status)) {
                set.add(status);
            }
        }
    });

    return Array.from(set);
}

// Which metric labels exist for each running mode
const METRIC_TABS_BY_MODE = {
    compare_to_reference: ['bgcs', 'fully', 'partial', 'missed'],
    compare_tools:        ['bgcs', 'unique', 'pyplots'],
    compare_samples:      ['bgcs']  // Overview only
};

// Which metric are we plotting (# BGCs, Fully recovered, etc.)
const METRIC_BASE = {
    bgcs:   '# BGCs',                 // existing behaviour
    fully:  'Fully recovered BGCs',
    partial:'Partially recovered BGCs',
    missed: 'Missed BGCs',
    unique: "Unique BGCs",
    // pyplots: no metricBase → handled specially
};

let currentMetricKey = 'bgcs';

function metricLabel(base, inside) {
    // e.g. base="# BGCs", inside="total"
    return `${base} (${inside})`;
}


/**
 * Build or rebuild the bar plot based on the current UI state.
 * @param {Array[]} data
 */
function buildBarPlotDynamic(data) {
    // If the current tab does not use a bar chart (e.g. "pyplots"), do nothing
    if (!METRIC_BASE[currentMetricKey]) {
        return;
    }

    const metricBase = METRIC_BASE[currentMetricKey];

    // In COMPARE_TO_REFERENCE, drop the last (reference) column from the plot for all tabs except Overview (totals)
    const hideReferenceForThisMetric =
        isReferenceMode && currentMetricKey !== 'bgcs';
    const colEnd = hideReferenceForThisMetric ? -1 : undefined;

    // labels are Assembly+Tool
    const tools = data[1].slice(1, colEnd);
    const assemblies = data[0].slice(1, colEnd);
    const labels = tools.map((tool, i) => `${tool}\n${assemblies[i]}`);

    // read UI
    const mode = document.getElementById('barModeShowBy').checked ? 'showby' : 'total';
    const byCompleteness = document.getElementById('byCompleteness').checked;
    const byType = document.getElementById('byType').checked;

    let datasets = [];

    if (mode === 'total') {
        const row = getRowByLabel(data, metricLabel(metricBase, 'total'));
        if (row) {
            const counts = row.slice(1, colEnd).map(v => parseInt(v, 10));
            datasets.push({
                label: metricLabel(metricBase, 'total'),
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
                // const rowComplete = getRowByLabel(data, `# BGCs (${type}, Complete)`);
                const rowComplete = getRowByLabel(data, metricLabel(metricBase, `${type}, Complete`));
                const rowIncomplete = getRowByLabel(data, metricLabel(metricBase, `${type}, Incomplete`));
                const rowUnknown    = getRowByLabel(data, metricLabel(metricBase, `${type}, Unknown completeness`));

                if (statuses.includes('complete') && rowComplete) {
                    datasets.push({
                        label: `${type} complete`,
                        data: rowComplete.slice(1, colEnd).map(v => parseInt(v, 10)),
                        backgroundColor: baseColor
                    });
                }
                if (statuses.includes('incomplete') && rowIncomplete) {
                    datasets.push({
                        label: `${type} incomplete`,
                        data: rowIncomplete.slice(1, colEnd).map(v => parseInt(v, 10)),
                        backgroundColor: lighten(baseColor, 0.45) // lighter shade
                    });
                }
                if (statuses.includes('unknown completeness') && rowUnknown) {
                    datasets.push({
                        label: `${type} unknown completeness`,
                        data: rowUnknown.slice(1, colEnd).map(v => parseInt(v, 10)),
                        backgroundColor: lighten(baseColor, 0.75) // even lighter shade
                    });
                }
            }
        } else if (byCompleteness) {
            // stacks are complete vs incomplete (total)
            const rowComplete   = getRowByLabel(data, metricLabel(metricBase, 'Complete'));
            const rowIncomplete = getRowByLabel(data, metricLabel(metricBase, 'Incomplete'));
            const rowUnknown    = getRowByLabel(data, metricLabel(metricBase, 'Unknown completeness'));
            const statuses = selectedStatusesFromUI();

            if (statuses.includes('complete') && rowComplete) {
                datasets.push({
                    label: 'Complete',
                    data: rowComplete.slice(1, colEnd).map(v => parseInt(v, 10)),
                    backgroundColor: '#578c18'
                });
            }
            if (statuses.includes('incomplete') && rowIncomplete) {
                datasets.push({
                    label: 'Incomplete',
                    data: rowIncomplete.slice(1, colEnd).map(v => parseInt(v, 10)),
                    backgroundColor: '#ccca3d'
                });
            }
            if (statuses.includes('unknown completeness') && rowUnknown) {
                datasets.push({
                    label: 'Unknown completeness',
                    data: rowUnknown.slice(1, colEnd).map(v => parseInt(v, 10)),
                    backgroundColor: '#999999'
                });
            }

        } else if (byType) {
            // stacks are by type (totals per type)
            const allTypes = detectTypes(data);
            const types = selectedTypesFromUI(allTypes);
            for (const type of types) {
                const row = getRowByLabel(data, metricLabel(metricBase, type));
                if (row) {
                    datasets.push({
                        label: type,
                        data: row.slice(1, colEnd).map(v => parseInt(v, 10)),
                        backgroundColor: productColors[type] || productColors['Other']
                    });
                }
            }
        } else {
            // fallback: if user selected "Show by" but no boxes,
            // just show the *current metric* total to avoid an empty chart.
            const row = getRowByLabel(data, metricLabel(metricBase, 'total'));
            if (row) {
                const counts = row.slice(1, colEnd).map(v => parseInt(v, 10));
                datasets.push({
                    label: metricLabel(metricBase, 'total'),
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


/* ---------------------------------------------------------------------------
 * PAGE INITIALIZATION & EVENT WIRING
 * ------------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    buildTable(reportData);
    renderTypeFilters(detectTypes(reportData));
    renderCompletenessFilters(detectCompleteness(reportData));
    buildBarPlotDynamic(reportData);

    // Extended report toggle visibility (show/hide extra rows)
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

    // Heatmap toggle
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


    // Metric tabs: which ones are visible depends on running mode
    const allMetricTabs = Array.from(document.querySelectorAll('.metric-tab'));
    const mode = (typeof reportMode === 'string') ? reportMode : 'compare_samples';
    const allowedKeys = METRIC_TABS_BY_MODE[mode] || ['bgcs'];

    // Populate pythonPlotsPanel (compare_tools mode only)
    if (mode === 'compare_tools') {
        const pythonPanel = document.getElementById('pythonPlotsPanel');
        if (pythonPanel && Array.isArray(pythonPlots)) {
            if (pythonPlots.length > 0) {
                pythonPlots.forEach(src => {
                    const img = document.createElement('img');
                    img.src = src;
                    img.classList.add('python-plot');
                    pythonPanel.appendChild(img);
                });
            } else {
                // Optional: message when no PNGs found
                const msg = document.createElement('p');
                msg.textContent = 'No additional plots available.';
                pythonPanel.appendChild(msg);
            }
        }
    }

    // Show/hide buttons according to mode
    allMetricTabs.forEach(btn => {
        const key = btn.dataset.metric;
        const visible = allowedKeys.includes(key);
        btn.style.display = visible ? '' : 'none';
    });

    // The default active tab is always "Overview"
    currentMetricKey = 'bgcs';
    const overviewBtn = allMetricTabs.find(b => b.dataset.metric === 'bgcs');
    if (overviewBtn) {
        allMetricTabs.forEach(b => b.classList.toggle('active', b === overviewBtn));
    }

    // Click handling (bar chart vs python plots)
    allMetricTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.metric;
            if (!allowedKeys.includes(key)) return;

            currentMetricKey = key;

            allMetricTabs.forEach(b => b.classList.toggle('active', b === btn));

            const chartCanvas = document.getElementById('bgcBarPlot');
            const pythonPanel = document.getElementById('pythonPlotsPanel');
            const controls    = document.querySelector('.barplot-controls');

            if (key === 'pyplots') {
                // Show python-generated PNGs, hide bar chart
                if (chartCanvas) chartCanvas.style.display = 'none';
                if (pythonPanel) pythonPanel.style.display = 'block';
                if (controls)    controls.style.display    = 'none';

                // Optional: destroy existing chart
                if (bgcChart) {
                    bgcChart.destroy();
                    bgcChart = null;
                }
            } else {
                // Show bar chart, hide python PNGs
                if (chartCanvas) chartCanvas.style.display = 'block';
                if (pythonPanel) pythonPanel.style.display = 'none';
                if (controls)    controls.style.display    = '';

                buildBarPlotDynamic(reportData);
            }
        });
    });


    // Bar plot controls listeners
    // "Show by" controls: radio buttons & "by ..." checkboxes
    ['barModeTotal','barModeShowBy','byCompleteness','byType'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => {
            syncShowByDisabled();
            buildBarPlotDynamic(reportData);
        });
    });

    // Product type checkbox changes
    const typeGroup = document.getElementById('typeFilterGroup');
    if (typeGroup) {
        typeGroup.addEventListener('change', (e) => {
            if (e.target && e.target.matches('input[type="checkbox"]')) {
                buildBarPlotDynamic(reportData);
            }
        });
    }

    // Completeness checkbox changes
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

    // Draw heatmap gradient
    drawHeatmapLegend(60, 280);  // yellow to purple


});
