/**
 * Web Data Extractor - Main JavaScript File
 * Handles form submission, API calls, and UI interactions
 */

// ================================================
// Configuration
// ================================================

const API_BASE_URL = '/';
const SCRAPE_ENDPOINT = '/scrape';
const DOWNLOAD_ENDPOINT = '/download';

let currentScrapedData = [];
let currentScrapedHeaders = [];
let discoveredPages = [];

// ================================================
// Initialization
// ================================================

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('Initializing Web Data Extractor Application...');
    
    // Get DOM elements
    const scraperForm = document.getElementById('scraperForm');
    const clearResultsBtn = document.getElementById('clearResultsBtn');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    const autoDiscoverCheck = document.getElementById('autoDiscoverCheck');
    const discoverPagesBtn = document.getElementById('discoverPagesBtn');
    
    // Attach event listeners
    if (scraperForm) {
        scraperForm.addEventListener('submit', handleFormSubmit);
    }
    
    if (clearResultsBtn) {
        clearResultsBtn.addEventListener('click', clearResults);
    }
    
    if (downloadCsvBtn) {
        downloadCsvBtn.addEventListener('click', downloadAsCSV);
    }
    
    // Auto-discovery listeners
    if (autoDiscoverCheck) {
        autoDiscoverCheck.addEventListener('change', handleAutoDiscoverToggle);
    }
    
    if (discoverPagesBtn) {
        discoverPagesBtn.addEventListener('click', handleDiscoverPages);
    }
    
    console.log('Application initialized successfully');
}

// ================================================
// Form Handling
// ================================================

/**
 * Handle form submission for scraping
 * @param {Event} event - Form submission event
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    console.log('Form submitted');
    
    // Get form values
    const urlInput = document.getElementById('urlInput').value.trim();
    const pagesInput = parseInt(document.getElementById('pagesInput').value) || 1;
    
    // Validate inputs
    if (!validateInputs(urlInput)) {
        return;
    }
    
    // Clear previous alerts and results
    clearAlerts();
    
    // Show loading indicator
    showLoadingIndicator();
    
    try {
        // Prepare request data (selector is optional - will scrape all content)
        const requestData = {
            url: urlInput,
            pages: pagesInput
        };
        
        console.log('Sending scrape request:', requestData);
        
        // Make API call
        const response = await fetch(SCRAPE_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        // Parse response
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Scraping failed');
        }
        
        console.log('Scrape successful:', result);
        
        // Handle successful response
        if (result.success) {
            handleScrapingSuccess(result);
        } else {
            showAlert(result.message || 'Scraping failed', 'danger');
        }
        
    } catch (error) {
        console.error('Scraping error:', error);
        showAlert(error.message || 'An error occurred during scraping', 'danger');
    } finally {
        hideLoadingIndicator();
        updateSubmitButtonState();
    }
}

/**
 * Validate form inputs
 * @param {string} url - Website URL
 * @returns {boolean} - Whether inputs are valid
 */
function validateInputs(url) {
    // Validate URL format
    if (!url) {
        showAlert('Please enter a website URL', 'warning');
        return false;
    }
    
    // Check if URL starts with http or https
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        showAlert('URL must start with http:// or https://', 'warning');
        return false;
    }
    
    // Validate URL format using regex
    const urlRegex = /^https?:\/\/.+/;
    if (!urlRegex.test(url)) {
        showAlert('Invalid URL format', 'warning');
        return false;
    }
    
    return true;
}

/**
 * Handle successful scraping response
 * @param {Object} result - API response
 */
function handleScrapingSuccess(result) {
    // Extract data from result
    const data = result.data || [];
    
    if (data.length === 0) {
        showAlert('No data found with the given selector', 'info');
        return;
    }
    
    // Store data for later use
    currentScrapedData = data;
    
    // Extract headers from first data item
    if (Array.isArray(data[0])) {
        // If data is array of arrays, use indices as headers
        currentScrapedHeaders = Array.from({length: data[0].length}, (_, i) => `Column ${i + 1}`);
    } else if (typeof data[0] === 'object') {
        // If data is array of objects, use object keys as headers
        currentScrapedHeaders = Object.keys(data[0]);
    } else {
        // If data is array of primitives, use single header
        currentScrapedHeaders = ['Content'];
    }
    
    // Display results
    displayResults(data, currentScrapedHeaders);
    
    // Show success message
    showAlert(`Successfully extracted ${data.length} items`, 'success');
}

// ================================================
// Display Results
// ================================================

/**
 * Display scraped data in the results table
 * @param {Array} data - Scraped data
 * @param {Array} headers - Column headers
 */
function displayResults(data, headers) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsTableContainer = document.getElementById('resultsTableContainer');
    const tableHead = document.getElementById('tableHead');
    const tableBody = document.getElementById('tableBody');
    const resultCount = document.getElementById('resultCount');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const downloadCsvBtn = document.getElementById('downloadCsvBtn');
    
    // Clear previous results
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Update result count
    resultCount.textContent = data.length;
    
    // Create table headers
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        th.style.maxWidth = '200px';
        th.style.wordWrap = 'break-word';
        headerRow.appendChild(th);
    });
    tableHead.appendChild(headerRow);
    
    // Limit displayed rows for performance
    const maxDisplayRows = 1000;
    const rowsToDisplay = Math.min(data.length, maxDisplayRows);
    
    // Create table rows
    for (let i = 0; i < rowsToDisplay; i++) {
        const row = document.createElement('tr');
        const item = data[i];
        
        if (Array.isArray(item)) {
            // Handle array data
            item.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = sanitizeValue(cell);
                td.style.maxWidth = '200px';
                td.style.wordWrap = 'break-word';
                row.appendChild(td);
            });
        } else if (typeof item === 'object' && item !== null) {
            // Handle object data
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = sanitizeValue(item[header]);
                td.style.maxWidth = '200px';
                td.style.wordWrap = 'break-word';
                row.appendChild(td);
            });
        } else {
            // Handle primitive data
            const td = document.createElement('td');
            td.textContent = sanitizeValue(item);
            row.appendChild(td);
        }
        
        tableBody.appendChild(row);
    }
    
    // Show/hide appropriate sections
    if (data.length === 0) {
        noResultsMessage.style.display = 'block';
        resultsTableContainer.style.display = 'none';
        downloadCsvBtn.style.display = 'none';
    } else {
        noResultsMessage.style.display = 'none';
        resultsTableContainer.style.display = 'block';
        downloadCsvBtn.style.display = 'inline-flex';
    }
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({behavior: 'smooth', block: 'start'});
}

/**
 * Sanitize and format cell values
 * @param {any} value - Cell value
 * @returns {string} - Formatted value
 */
function sanitizeValue(value) {
    if (value === null || value === undefined) {
        return '';
    }
    
    // Convert to string and limit length
    let str = String(value).trim();
    
    // Limit to 500 characters for display
    if (str.length > 500) {
        str = str.substring(0, 497) + '...';
    }
    
    return str;
}

// ================================================
// Download CSV
// ================================================

/**
 * Download scraped data as CSV
 */
function downloadAsCSV() {
    if (currentScrapedData.length === 0) {
        showAlert('No data to download', 'warning');
        return;
    }
    
    try {
        // Convert data to CSV format
        const csv = generateCSV(currentScrapedData, currentScrapedHeaders);
        
        // Create blob and download
        const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
        const filename = `extracted-data-${timestamp}.csv`;
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('CSV downloaded:', filename);
        showAlert(`Downloaded as ${filename}`, 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showAlert('Failed to download CSV', 'danger');
    }
}

/**
 * Generate CSV content from data
 * @param {Array} data - Data to convert
 * @param {Array} headers - Column headers
 * @returns {string} - CSV content
 */
function generateCSV(data, headers) {
    let csv = '';
    
    // Add headers
    csv += headers.map(h => escapeCSVField(String(h))).join(',') + '\n';
    
    // Add data rows
    data.forEach(item => {
        if (Array.isArray(item)) {
            csv += item.map(cell => escapeCSVField(String(cell || ''))).join(',') + '\n';
        } else if (typeof item === 'object' && item !== null) {
            const row = headers.map(header => escapeCSVField(String(item[header] || '')));
            csv += row.join(',') + '\n';
        } else {
            csv += escapeCSVField(String(item || '')) + '\n';
        }
    });
    
    return csv;
}

/**
 * Escape CSV field values
 * @param {string} field - Field value
 * @returns {string} - Escaped field
 */
function escapeCSVField(field) {
    // If field contains comma, newline, or quotes, wrap in quotes
    if (field.includes(',') || field.includes('\n') || field.includes('"')) {
        // Escape quotes by doubling them
        return '"' + field.replace(/"/g, '""') + '"';
    }
    return field;
}

// ================================================
// Alert Messages
// ================================================

/**
 * Show alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span class="alert-message">${escapeHtml(message)}</span>
        <span class="alert-close" onclick="this.parentElement.remove();">×</span>
    `;
    
    alertContainer.appendChild(alert);
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Auto-remove info and success alerts after 5 seconds
    if (type === 'info' || type === 'success') {
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

/**
 * Clear all alerts
 */
function clearAlerts() {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = '';
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ================================================
// Loading Indicator
// ================================================

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    
    loadingIndicator.style.display = 'flex';
    resultsSection.style.display = 'block';
    
    updateSubmitButtonState(true);
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'none';
}

/**
 * Update submit button state
 * @param {boolean} isLoading - Whether loading
 */
function updateSubmitButtonState(isLoading = false) {
    const submitBtn = document.getElementById('scraperSubmitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = document.getElementById('btnLoader');
    
    if (isLoading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-flex';
    } else {
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// ================================================
// Clear Results
// ================================================

/**
 * Clear results and reset display
 */
function clearResults() {
    const resultsSection = document.getElementById('resultsSection');
    const resultsTableContainer = document.getElementById('resultsTableContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');
    
    // Clear data
    currentScrapedData = [];
    currentScrapedHeaders = [];
    
    // Clear table
    document.getElementById('tableHead').innerHTML = '';
    document.getElementById('tableBody').innerHTML = '';
    
    // Hide sections
    resultsTableContainer.style.display = 'none';
    noResultsMessage.style.display = 'none';
    resultsSection.style.display = 'none';
    
    // Clear alerts
    clearAlerts();
    
    console.log('Results cleared');
}

// ================================================
// Utility Functions
// ================================================

/**
 * Format number with commas
 * @param {number} num - Number to format
 * @returns {string} - Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// ================================================
// Event Listeners
// ================================================

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// Log page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden');
    } else {
        console.log('Page visible');
    }
});

// ================================================
// Auto-Discovery Functions
// ================================================

/**
 * Handle auto-discover toggle
 */
function handleAutoDiscoverToggle(event) {
    const isEnabled = event.target.checked;
    const discoverPagesBtn = document.getElementById('discoverPagesBtn');
    const pagesInputGroup = document.getElementById('pagesInputGroup');
    const discoveredPagesSection = document.getElementById('discoveredPagesSection');
    
    if (isEnabled) {
        // Show discover button, hide manual pages input
        discoverPagesBtn.style.display = 'inline-block';
        pagesInputGroup.style.display = 'none';
        
        // Auto-discover pages when enabled
        handleDiscoverPages();
    } else {
        // Hide discover button and discovered pages, show manual input
        discoverPagesBtn.style.display = 'none';
        discoveredPagesSection.style.display = 'none';
        pagesInputGroup.style.display = 'block';
        
        // Clear discovered pages
        discoveredPages = [];
    }
}

/**
 * Handle discover pages button click
 */
async function handleDiscoverPages() {
    const urlInput = document.getElementById('urlInput').value.trim();
    
    if (!validateInputs(urlInput)) {
        return;
    }
    
    clearAlerts();
    showDiscoveryLoading(true);
    
    try {
        console.log('Discovering pages for:', urlInput);
        
        // Call discovery endpoint
        const response = await fetch('/discover-pages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: urlInput })
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Failed to discover pages');
        }
        
        discoveredPages = result.pages || [];
        console.log('Discovered pages:', discoveredPages);
        
        displayDiscoveredPages(discoveredPages);
        showAlert(`Discovered ${discoveredPages.length} pages`, 'success');
        
    } catch (error) {
        console.error('Discovery error:', error);
        showAlert(error.message || 'Failed to discover pages', 'danger');
    } finally {
        showDiscoveryLoading(false);
    }
}

/**
 * Display discovered pages
 * @param {Array} pages - Discovered pages
 */
function displayDiscoveredPages(pages) {
    const discoveredPagesSection = document.getElementById('discoveredPagesSection');
    const pagesList = document.getElementById('pagesList');
    
    pagesList.innerHTML = '';
    
    if (pages.length === 0) {
        pagesList.innerHTML = '<p style="color: #7f8c8d;">No pages discovered</p>';
        discoveredPagesSection.style.display = 'block';
        return;
    }
    
    // Auto-select first 5 pages
    pages.forEach((page, index) => {
        const pageItem = document.createElement('div');
        pageItem.className = 'page-item';
        
        // Auto-check first 5
        const isChecked = index < 5;
        
        pageItem.innerHTML = `
            <input 
                type="checkbox" 
                class="page-checkbox" 
                value="${index}"
                ${isChecked ? 'checked' : ''}
            >
            <label class="page-item-label">
                <strong>${page.title || `Page ${index + 1}`}</strong>
                <small>${page.url}</small>
            </label>
        `;
        
        if (isChecked) {
            pageItem.classList.add('selected');
        }
        
        // Add change listener
        const checkbox = pageItem.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                pageItem.classList.add('selected');
            } else {
                pageItem.classList.remove('selected');
            }
        });
        
        pagesList.appendChild(pageItem);
    });
    
    discoveredPagesSection.style.display = 'block';
}

/**
 * Show/hide discovery loading indicator
 * @param {boolean} show - Whether to show
 */
function showDiscoveryLoading(show) {
    const discoveryLoadingIndicator = document.getElementById('discoveryLoadingIndicator');
    if (discoveryLoadingIndicator) {
        discoveryLoadingIndicator.style.display = show ? 'flex' : 'none';
    }
}

/**
 * Get selected pages for scraping
 * @returns {Array} - Selected page URLs
 */
function getSelectedPages() {
    const checkboxes = document.querySelectorAll('.page-checkbox:checked');
    const selectedPages = [];
    
    checkboxes.forEach(checkbox => {
        const index = parseInt(checkbox.value);
        if (discoveredPages[index]) {
            selectedPages.push(discoveredPages[index].url);
        }
    });
    
    return selectedPages;
}

/**
 * Override form submission to handle discovered pages
 */
document.addEventListener('DOMContentLoaded', function() {
    const scraperForm = document.getElementById('scraperForm');
    const originalFormHandler = scraperForm.onsubmit;
    
    scraperForm.addEventListener('submit', async function(event) {
        const autoDiscoverCheck = document.getElementById('autoDiscoverCheck');
        
        if (autoDiscoverCheck && autoDiscoverCheck.checked) {
            event.preventDefault();
            
            const selectedPages = getSelectedPages();
            if (selectedPages.length === 0) {
                showAlert('Please select at least one page to scrape', 'warning');
                return;
            }
            
            console.log('Scraping selected pages:', selectedPages);
            
            clearAlerts();
            showLoadingIndicator();
            
            try {
                // Scrape multiple pages
                const urlInput = document.getElementById('urlInput').value.trim();
                
                const requestData = {
                    url: urlInput,
                    pages: selectedPages.length,
                    discover: true,
                    selected_pages: selectedPages
                };
                
                const response = await fetch(SCRAPE_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.message || 'Scraping failed');
                }
                
                if (result.success) {
                    handleScrapingSuccess(result);
                } else {
                    showAlert(result.message || 'Scraping failed', 'danger');
                }
                
            } catch (error) {
                console.error('Scraping error:', error);
                showAlert(error.message || 'An error occurred during scraping', 'danger');
            } finally {
                hideLoadingIndicator();
                updateSubmitButtonState();
            }
        }
    });
});
