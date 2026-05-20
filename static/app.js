// Global State
let calculatedChart = null;
let queryCounter = 1;
let currentTab = 'category';

// Planet short names and classifications
const PLANET_METADATA = {
    "Sun": { short: "Su", malefic: true },
    "Moon": { short: "Mo", malefic: false },
    "Mars": { short: "Ma", malefic: true },
    "Mercury": { short: "Me", malefic: false },
    "Jupiter": { short: "Ju", malefic: false },
    "Venus": { short: "Ve", malefic: false },
    "Saturn": { short: "Sa", malefic: true },
    "Rahu": { short: "Ra", malefic: true },
    "Ketu": { short: "Ke", malefic: true }
};

// Coordinate offsets for rendering elements inside North Indian houses (400x400 SVG)
// cx/cy = Center for planets, sx/sy = Corner for Sign numbers
const HOUSE_GEOMETRY = {
    1:  { cx: 200, cy: 90,  sx: 200, sy: 135 }, // Top Center
    2:  { cx: 125, cy: 50,  sx: 150, sy: 75  }, // Top Left
    3:  { cx: 65,  cy: 110, sx: 90,  sy: 135 }, // Left Top
    4:  { cx: 110, cy: 200, sx: 150, sy: 200 }, // Left Center
    5:  { cx: 65,  cy: 290, sx: 90,  sy: 265 }, // Left Bottom
    6:  { cx: 125, cy: 350, sx: 150, sy: 325 }, // Bottom Left
    7:  { cx: 200, cy: 310, sx: 200, sy: 265 }, // Bottom Center
    8:  { cx: 275, cy: 350, sx: 250, sy: 325 }, // Bottom Right
    9:  { cx: 335, cy: 290, sx: 310, sy: 265 }, // Right Bottom
    10: { cx: 290, cy: 200, sx: 250, sy: 200 }, // Right Center
    11: { cx: 335, cy: 110, sx: 310, sy: 135 }, // Right Top
    12: { cx: 275, cy: 50,  sx: 250, sy: 75  }  // Top Right
};

// Initialize form defaults on load
window.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    
    // Set Local Date input default (YYYY-MM-DD)
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    document.getElementById('date').value = `${yyyy}-${mm}-${dd}`;
    
    // Set Local Time input default (HH:MM:SS)
    const hh = String(today.getHours()).padStart(2, '0');
    const min = String(today.getMinutes()).padStart(2, '0');
    const sec = String(today.getSeconds()).padStart(2, '0');
    document.getElementById('time').value = `${hh}:${min}:${sec}`;
    
    // Determine timezone offset automatically in hours (positive for East, negative for West)
    const tzMin = -today.getTimezoneOffset();
    document.getElementById('tz_offset').value = tzMin / 60;
    
    setupFormListeners();
    setupLocationAutocomplete();
});




// Setup Form Submission Listeners
function setupFormListeners() {
    const chartForm = document.getElementById('chart-form');
    const evaluateBtn = document.getElementById('evaluate-btn');
    
    chartForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const calculateBtn = document.getElementById('calculate-btn');
        calculateBtn.disabled = true;
        calculateBtn.innerHTML = '<span>Calculating...</span>';
        
        const date = document.getElementById('date').value;
        const time = document.getElementById('time').value;
        const tz_offset = parseFloat(document.getElementById('tz_offset').value);
        const latitude = document.getElementById('latitude').value;
        const longitude = document.getElementById('longitude').value;
        
        try {
            const res = await fetch('/api/chart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, time, tz_offset, latitude, longitude })
            });
            
            const data = await res.json();
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                calculatedChart = data;
                renderKundali(data);
                renderPlanetsTable(data);
                evaluateBtn.disabled = false;
                
                // Clear any old readings
                document.getElementById('ai-section').classList.add('hidden');
                document.getElementById('results-content').classList.add('hidden');
                document.getElementById('results-placeholder').classList.remove('hidden');
            }
        } catch (err) {
            alert(`Communication failure: ${err}`);
        } finally {
            calculateBtn.disabled = false;
            calculateBtn.innerHTML = '<span>Calculate Prasna Chart</span>';
        }
    });
    
    evaluateBtn.addEventListener('click', handleEvaluation);
}

// Dynamic rendering of North Indian Kundali SVG
function renderKundali(chart) {
    const container = document.getElementById('chart-dynamic-content');
    container.innerHTML = ''; // Clear old content
    
    // 1. Render sign numbers in each house
    // Whole sign: sign = (LagnaSign + HouseNumber - 1) % 12 + 1
    const lagnaSign = chart.lagna_sign; // 0-indexed (0=Aries)
    
    for (let h = 1; h <= 12; h++) {
        const signNum = ((lagnaSign + h - 1) % 12) + 1; // 1-indexed (1=Aries)
        const geom = HOUSE_GEOMETRY[h];
        
        const textNode = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textNode.setAttribute('x', geom.sx);
        textNode.setAttribute('y', geom.sy);
        textNode.setAttribute('class', 'sign-number');
        textNode.textContent = signNum;
        container.appendChild(textNode);
    }
    
    // 2. Render planets in their respective houses
    // Group planets by house occupancy
    const houseOccupants = {};
    for (let h = 1; h <= 12; h++) {
        houseOccupants[h] = [];
    }
    
    // Determine which house each planet is situated in (Whole Sign)
    // House = (PlanetSign - LagnaSign + 12) % 12 + 1
    Object.keys(chart.planets).forEach(pName => {
        const pData = chart.planets[pName];
        const pSign = pData.sign; // 0-indexed
        const pHouse = ((pSign - lagnaSign + 12) % 12) + 1;
        
        const meta = PLANET_METADATA[pName] || { short: pName.substring(0, 2), malefic: false };
        let label = meta.short;
        if (pData.speed < 0) {
            label += "(R)"; // Retrograde
        }
        if (pData.avastha === "Mushita") {
            label += "c"; // Combust
        }
        
        houseOccupants[pHouse].push({
            name: pName,
            label: label,
            isMalefic: meta.malefic,
            isCombust: pData.avastha === "Mushita"
        });
    });
    
    // Render occupants inside each house
    for (let h = 1; h <= 12; h++) {
        const occupants = houseOccupants[h];
        if (occupants.length === 0) continue;
        
        const geom = HOUSE_GEOMETRY[h];
        const numOcc = occupants.length;
        
        occupants.forEach((occ, idx) => {
            const textNode = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            textNode.setAttribute('x', geom.cx);
            
            // Adjust y offset based on index to stack them
            let yOffset = geom.cy;
            if (numOcc > 1) {
                yOffset = geom.cy - ((numOcc - 1) * 7) + (idx * 14);
            }
            
            textNode.setAttribute('y', yOffset);
            
            let cssClass = 'planet-txt';
            if (occ.isMalefic) cssClass += ' malefic';
            else cssClass += ' benefic';
            
            textNode.setAttribute('class', cssClass);
            textNode.textContent = occ.label;
            
            // Tooltip or title for hover
            const titleNode = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            titleNode.textContent = `${occ.name} ${occ.isCombust ? '(Combust)' : ''}`;
            textNode.appendChild(titleNode);
            
            container.appendChild(textNode);
        });
    }
    
    // 3. Set global meta
    document.getElementById('meta-ayan').textContent = chart.ayanamsha_formatted;
    document.getElementById('meta-lagna').textContent = `${chart.lagna_longitude_formatted} in ${chart.lagna_sign_name}`;
}

// Populate Planets Table
function renderPlanetsTable(chart) {
    const tableSection = document.getElementById('table-section');
    const tbody = document.getElementById('planets-tbody');
    tbody.innerHTML = '';
    
    // Insert Lagna row
    const lagnaRow = document.createElement('tr');
    lagnaRow.innerHTML = `
        <td>Lagna (Ascendant)</td>
        <td>${chart.lagna_longitude_formatted}</td>
        <td>${chart.lagna_sign_name}</td>
        <td>—</td>
        <td>—</td>
        <td>—</td>
        <td>—</td>
    `;
    tbody.appendChild(lagnaRow);
    
    // Insert planet rows
    Object.keys(chart.planets).forEach(pName => {
        const pData = chart.planets[pName];
        const tr = document.createElement('tr');
        
        let speedStr = pData.speed.toFixed(4);
        if (pData.speed < 0) {
            speedStr += " (Retro)";
        }
        
        tr.innerHTML = `
            <td>${pName}</td>
            <td>${pData.formatted}</td>
            <td>${pData.sign_name}</td>
            <td>${pData.nakshatra}</td>
            <td>${pData.pada}</td>
            <td style="font-weight: 500;">${pData.avastha}</td>
            <td>${speedStr}</td>
        `;
        tbody.appendChild(tr);
    });
    
    tableSection.classList.remove('hidden');
}

// Handle Astrological Evaluation Submit
async function handleEvaluation() {
    const evaluateBtn = document.getElementById('evaluate-btn');
    evaluateBtn.disabled = true;
    evaluateBtn.innerHTML = '<span>Evaluating...</span>';
    
    // Fetch input values
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const tz_offset = parseFloat(document.getElementById('tz_offset').value);
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    
    let houseNum = 1;
    let queryNum = queryCounter;
    let specialCategory = null;
    
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsContent = document.getElementById('results-content');
    
    resultsPlaceholder.classList.add('hidden');
    resultsContent.classList.add('hidden');
    
    const question = document.getElementById('free-question').value.trim();
    if (!question) {
        alert("Please enter a question.");
        evaluateBtn.disabled = false;
        evaluateBtn.innerHTML = '<span>Evaluate Query</span>';
        resultsPlaceholder.classList.remove('hidden');
        return;
    }
    
    try {
        // Map the free text question to a house
        const mapRes = await fetch('/api/map-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const mapping = await mapRes.json();
        if (mapping.error) {
            alert(`AI question mapping failed: ${mapping.error}. Defaulting to House 1.`);
            houseNum = 1;
        } else {
            houseNum = mapping.house;
            // If the mapped house has special rules, use them
            if (houseNum === 12) specialCategory = "deity_curse";
            else if (houseNum === 6) specialCategory = "master_servant";
            else if (houseNum === 1) specialCategory = "meals";
            else if (houseNum === 7) specialCategory = "sports";
            else if (houseNum === 8) specialCategory = "disputes";
            else if (houseNum === 4) specialCategory = "crops_trade";
        }
        
        // Execute horary evaluation
        const evalRes = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, time, tz_offset, latitude, longitude, house_num: houseNum, query_num: queryNum, special_category: specialCategory })
        });
        
        const evalData = await evalRes.json();
        if (evalData.error) {
            alert(`Evaluation failed: ${evalData.error}`);
            resultsPlaceholder.classList.remove('hidden');
        } else {
            displayEvaluationResults(evalData, question);
            // Stream the reading
            triggerAIReading(question, evalData);
            queryCounter++; // Increment query index for sequential shifts
        }
    } catch (err) {
        alert(`Evaluation error: ${err}`);
        resultsPlaceholder.classList.remove('hidden');
    } finally {
        evaluateBtn.disabled = false;
        evaluateBtn.innerHTML = '<span>Evaluate Query</span>';
    }
}

// Display results in right-side card
function displayEvaluationResults(data, question) {
    const content = document.getElementById('results-content');
    
    // Set headers
    document.getElementById('eval-header').classList.remove('hidden');
    document.getElementById('eval-title').textContent = `Query #${data.query_num}: House ${data.house}`;
    document.getElementById('eval-ref-point').textContent = `Shifted Reference: ${data.ref_point_name} (Sign: ${data.ref_sign_name}) ➔ Target Sign: ${data.query_sign_name}`;
    
    // Set metrics
    document.getElementById('metric-prob').textContent = data.success_probability;
    document.getElementById('metric-score').textContent = `${data.score_pct}%`;
    
    // Sincerity handling
    const sincVal = document.getElementById('metric-sincere');
    const sincBox = document.getElementById('results-content');
    const sincList = document.getElementById('sincerity-indicators');
    
    sincList.innerHTML = '';
    if (data.sincerity.is_sincere) {
        sincVal.textContent = "Sincere";
        sincVal.style.color = "var(--color-green)";
        sincBox.classList.add('sincere-query');
        
        if (data.sincerity.reasons_sincere.length > 0) {
            data.sincerity.reasons_sincere.forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                sincList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = "General query sincerity verified.";
            sincList.appendChild(li);
        }
    } else {
        sincVal.textContent = "Insincere";
        sincVal.style.color = "var(--color-red)";
        sincBox.classList.remove('sincere-query');
        
        data.sincerity.reasons_insincere.forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            sincList.appendChild(li);
        });
    }
    
    // Timing
    document.getElementById('val-timing').textContent = data.timing;
    
    // Evaluation Details
    const detailsList = document.getElementById('val-details');
    detailsList.innerHTML = '';
    data.details.forEach(det => {
        const li = document.createElement('li');
        li.textContent = det;
        detailsList.appendChild(li);
    });
    
    // Shatpanchasika predictions
    const shatSection = document.getElementById('shat-section');
    const shatList = document.getElementById('val-shat');
    shatList.innerHTML = '';
    
    if (data.shatpanchasika_predictions && data.shatpanchasika_predictions.length > 0) {
        data.shatpanchasika_predictions.forEach(p => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>[${p.category}]</strong> ${p.prediction}`;
            shatList.appendChild(li);
        });
        shatSection.classList.remove('hidden');
    } else {
        shatSection.classList.add('hidden');
    }
    
    content.classList.remove('hidden');
}

// Stream Groq AI Astrological reading token-by-token
async function triggerAIReading(question, chartDetails) {
    const aiSection = document.getElementById('ai-section');
    const aiText = document.getElementById('ai-reading-text');
    
    aiSection.classList.remove('hidden');
    aiText.textContent = "[AI is connecting to Groq & reading the heavens...]";
    
    try {
        const response = await fetch('/api/reading', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, chart_details: chartDetails })
        });
        
        if (!response.ok) {
            aiText.textContent = `[AI Error] Could not connect to API server: status ${response.status}`;
            return;
        }
        
        aiText.textContent = ""; // Clear buffer
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            aiText.textContent += chunk;
            
            // Auto scroll down to keep live text visible if needed
            aiText.scrollTop = aiText.scrollHeight;
        }
    } catch (err) {
        aiText.textContent = `[AI Error] Streaming interrupted: ${err}`;
    }
}

// Location Autocomplete Search and Timezone Resolution
function setupLocationAutocomplete() {
    const locationInput = document.getElementById('location-input');
    const suggestionsBox = document.getElementById('location-suggestions');
    const advancedToggle = document.getElementById('advanced-toggle');
    const advancedPanel = document.getElementById('advanced-coordinates');
    
    let autocompleteTimeout = null;

    // Advanced Coordinates toggle
    advancedToggle.addEventListener('click', () => {
        if (advancedPanel.classList.contains('hidden')) {
            advancedPanel.classList.remove('hidden');
            advancedToggle.textContent = '✦ Hide Advanced Coordinates';
        } else {
            advancedPanel.classList.add('hidden');
            advancedToggle.textContent = '✦ Show Advanced Coordinates';
        }
    });

    // Input autocomplete listener with 300ms debounce
    locationInput.addEventListener('input', () => {
        clearTimeout(autocompleteTimeout);
        const query = locationInput.value.trim();
        
        if (query.length < 3) {
            suggestionsBox.classList.add('hidden');
            suggestionsBox.innerHTML = '';
            return;
        }
        
        autocompleteTimeout = setTimeout(() => {
            fetchLocations(query);
        }, 300);
    });

    // Close suggestions on outside click
    document.addEventListener('click', (e) => {
        if (e.target !== locationInput && e.target !== suggestionsBox) {
            suggestionsBox.classList.add('hidden');
        }
    });

    // Re-resolve timezone offset when query date or time shifts
    ['date', 'time'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            const lat = document.getElementById('latitude').value;
            const lon = document.getElementById('longitude').value;
            if (lat && lon) {
                resolveTimezone(lat, lon);
            }
        });
    });
}

// Query OpenStreetMap Nominatim Geocoding API
async function fetchLocations(query) {
    const suggestionsBox = document.getElementById('location-suggestions');
    try {
        const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5`;
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'PrasnaTantraAstrologyDashboard/1.0'
            }
        });
        if (!response.ok) return;
        const results = await response.json();
        displaySuggestions(results);
    } catch (err) {
        console.error('Error fetching locations:', err);
    }
}

// Render matched search outcomes in suggestions dropdown
function displaySuggestions(results) {
    const suggestionsBox = document.getElementById('location-suggestions');
    const locationInput = document.getElementById('location-input');
    suggestionsBox.innerHTML = '';
    
    if (results.length === 0) {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = 'No matching locations found';
        suggestionsBox.appendChild(item);
        suggestionsBox.classList.remove('hidden');
        return;
    }
    
    results.forEach(res => {
        const name = res.display_name;
        const lat = res.lat;
        const lon = res.lon;
        
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = name;
        item.addEventListener('click', () => {
            locationInput.value = name;
            suggestionsBox.classList.add('hidden');
            suggestionsBox.innerHTML = '';
            
            // Set coordinate values
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lon;
            
            // Query backend for timezone offset resolution
            resolveTimezone(lat, lon);
        });
        suggestionsBox.appendChild(item);
    });
    
    suggestionsBox.classList.remove('hidden');
}

// Request timezone resolution from Flask backend
async function resolveTimezone(lat, lon) {
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    
    try {
        const res = await fetch('/api/resolve-timezone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: lat, longitude: lon, date, time })
        });
        const data = await res.json();
        if (data.tz_offset !== undefined) {
            document.getElementById('tz_offset').value = data.tz_offset;
        }
    } catch (err) {
        console.error('Error resolving timezone:', err);
    }
}

