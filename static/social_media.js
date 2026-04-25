/**
 * Social Media Scraper - JavaScript Module
 * Handles social media profile and posts scraping
 */

// ================================================
// Configuration
// ================================================

const SOCIAL_API_BASE = '/social';
const SOCIAL_PROFILE_ENDPOINT = '/social/scrape-profile';
const SOCIAL_POSTS_ENDPOINT = '/social/scrape-posts';
const SOCIAL_PLATFORMS_ENDPOINT = '/social/platforms';

// ================================================
// Initialization
// ================================================

function initializeSocialMedia() {
    console.log('Initializing Social Media Module...');
    
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', handleTabSwitch);
    });
    
    // Social media tabs
    const socialTabBtns = document.querySelectorAll('.social-tab-btn');
    socialTabBtns.forEach(btn => {
        btn.addEventListener('click', handleSocialTabSwitch);
    });
    
    // Form handlers
    const profileForm = document.getElementById('socialProfileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileSubmit);
    }
    
    const postsForm = document.getElementById('socialPostsForm');
    if (postsForm) {
        postsForm.addEventListener('submit', handlePostsSubmit);
    }
    
    // Results handlers
    const clearSocialBtn = document.getElementById('clearSocialResultsBtn');
    if (clearSocialBtn) {
        clearSocialBtn.addEventListener('click', clearSocialResults);
    }
    
    const copySocialBtn = document.getElementById('copySocialDataBtn');
    if (copySocialBtn) {
        copySocialBtn.addEventListener('click', copySocialData);
    }
    
    console.log('Social Media Module initialized successfully');
}

// ================================================
// Tab Switching
// ================================================

function handleTabSwitch(event) {
    const tabName = event.target.dataset.tab;
    
    // Hide all sections
    document.getElementById('website-scraper').style.display = 'none';
    document.getElementById('social-scraper').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('socialResultsSection').style.display = 'none';
    
    // Remove active class
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected section
    if (tabName === 'website-scraper') {
        document.getElementById('website-scraper').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'block';
    } else if (tabName === 'social-scraper') {
        document.getElementById('social-scraper').style.display = 'block';
        document.getElementById('socialResultsSection').style.display = 'block';
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

function handleSocialTabSwitch(event) {
    const tabName = event.target.dataset.socialTab;
    
    // Hide all forms
    document.getElementById('socialProfileForm').style.display = 'none';
    document.getElementById('socialPostsForm').style.display = 'none';
    
    // Remove active class
    document.querySelectorAll('.social-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected form
    if (tabName === 'profile') {
        document.getElementById('socialProfileForm').style.display = 'block';
    } else if (tabName === 'posts') {
        document.getElementById('socialPostsForm').style.display = 'block';
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// ================================================
// Form Submission Handlers
// ================================================

async function handleProfileSubmit(event) {
    event.preventDefault();
    
    const platform = document.getElementById('platformSelect').value.trim();
    const username = document.getElementById('usernameInput').value.trim();
    
    if (!platform || !username) {
        showSocialAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    await scrapeProfile(platform, username);
}

async function handlePostsSubmit(event) {
    event.preventDefault();
    
    const platform = document.getElementById('postsPlatformSelect').value.trim();
    const username = document.getElementById('postsUsernameInput').value.trim();
    const limit = parseInt(document.getElementById('postsLimitInput').value) || 10;
    
    if (!platform || !username) {
        showSocialAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    await scrapePosts(platform, username, limit);
}

// ================================================
// API Calls
// ================================================

async function scrapeProfile(platform, username) {
    clearSocialAlerts();
    showSocialLoading(true);
    
    try {
        const response = await fetch(SOCIAL_PROFILE_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform.toLowerCase(),
                username: username
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showSocialAlert(`Error: ${data.message || 'Failed to scrape profile'}`, 'danger');
            showSocialLoading(false);
            return;
        }
        
        displayProfileResults(data);
        showSocialLoading(false);
        showSocialAlert('Profile scraped successfully!', 'success');
        
    } catch (error) {
        console.error('Error scraping profile:', error);
        showSocialAlert(`Error: ${error.message}`, 'danger');
        showSocialLoading(false);
    }
}

async function scrapePosts(platform, username, limit) {
    clearSocialAlerts();
    showSocialLoading(true);
    
    try {
        const response = await fetch(SOCIAL_POSTS_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform.toLowerCase(),
                username: username,
                limit: limit
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showSocialAlert(`Error: ${data.message || 'Failed to scrape posts'}`, 'danger');
            showSocialLoading(false);
            return;
        }
        
        displayPostsResults(data);
        showSocialLoading(false);
        showSocialAlert(`Successfully scraped ${data.count || 0} posts!`, 'success');
        
    } catch (error) {
        console.error('Error scraping posts:', error);
        showSocialAlert(`Error: ${error.message}`, 'danger');
        showSocialLoading(false);
    }
}

// ================================================
// Display Results
// ================================================

function displayProfileResults(data) {
    const profileContainer = document.getElementById('socialProfileResultsContainer');
    const postsContainer = document.getElementById('socialPostsResultsContainer');
    
    // Hide posts container, show profile
    postsContainer.style.display = 'none';
    profileContainer.style.display = 'block';
    
    // Update profile info
    document.getElementById('profileUsername').textContent = `@${data.username}`;
    document.getElementById('profilePlatform').textContent = data.platform.toUpperCase();
    
    const profileInfoContainer = document.getElementById('profileInfoContainer');
    profileInfoContainer.innerHTML = '';
    
    if (data.data) {
        for (const [key, value] of Object.entries(data.data)) {
            if (value !== null && value !== undefined && key !== 'note') {
                const infoItem = document.createElement('div');
                infoItem.className = 'info-item';
                infoItem.innerHTML = `
                    <div class="info-item-label">${formatLabel(key)}</div>
                    <div class="info-item-value">${formatValue(value)}</div>
                `;
                profileInfoContainer.appendChild(infoItem);
            }
        }
    }
    
    // Show results section
    document.getElementById('socialResultsSection').style.display = 'block';
    document.getElementById('copySocialDataBtn').style.display = 'inline-block';
}

function displayPostsResults(data) {
    const profileContainer = document.getElementById('socialProfileResultsContainer');
    const postsContainer = document.getElementById('socialPostsResultsContainer');
    
    // Hide profile container, show posts
    profileContainer.style.display = 'none';
    postsContainer.style.display = 'block';
    
    // Update results count
    document.getElementById('socialResultCount').textContent = data.count || 0;
    
    const postsListContainer = document.getElementById('postsListContainer');
    postsListContainer.innerHTML = '';
    
    if (data.data && Array.isArray(data.data)) {
        data.data.forEach((post, index) => {
            const postCard = document.createElement('div');
            postCard.className = 'post-card';
            
            const content = post.content || post.text || post.title || 'No content';
            const timestamp = post.timestamp || post.created_at || 'Unknown date';
            const likes = post.likes || post.engagement || 0;
            const comments = post.comments || 0;
            const shares = post.shares || post.reposts || 0;
            
            postCard.innerHTML = `
                <div class="post-header">
                    <span>📅 ${formatDate(timestamp)}</span>
                </div>
                <div class="post-content">${truncateText(content, 200)}</div>
                <div class="post-meta">
                    <div class="post-stats">
                        <div class="stat">
                            <span class="stat-value">${likes}</span>
                            <span>Likes</span>
                        </div>
                        <div class="stat">
                            <span class="stat-value">${comments}</span>
                            <span>Comments</span>
                        </div>
                        <div class="stat">
                            <span class="stat-value">${shares}</span>
                            <span>Shares</span>
                        </div>
                    </div>
                </div>
            `;
            
            postsListContainer.appendChild(postCard);
        });
    }
    
    // Show results section
    document.getElementById('socialResultsSection').style.display = 'block';
}

// ================================================
// Alert Messages
// ================================================

function clearSocialAlerts() {
    const alertContainer = document.getElementById('socialAlertContainer');
    alertContainer.innerHTML = '';
}

function showSocialAlert(message, type = 'info') {
    const alertContainer = document.getElementById('socialAlertContainer');
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// ================================================
// Loading Indicator
// ================================================

function showSocialLoading(show) {
    const loadingIndicator = document.getElementById('socialLoadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'flex' : 'none';
    }
}

// ================================================
// Clear Results
// ================================================

function clearSocialResults() {
    document.getElementById('socialProfileResultsContainer').style.display = 'none';
    document.getElementById('socialPostsResultsContainer').style.display = 'none';
    document.getElementById('socialErrorMessage').style.display = 'none';
    document.getElementById('copySocialDataBtn').style.display = 'none';
    clearSocialAlerts();
}

// ================================================
// Copy Data
// ================================================

function copySocialData() {
    let dataToCopy = '';
    
    const profileContainer = document.getElementById('socialProfileResultsContainer');
    const postsContainer = document.getElementById('socialPostsResultsContainer');
    
    if (profileContainer.style.display !== 'none') {
        // Copy profile data
        const username = document.getElementById('profileUsername').textContent;
        const platform = document.getElementById('profilePlatform').textContent;
        dataToCopy = `${username} - ${platform}\n\n`;
        
        document.querySelectorAll('#profileInfoContainer .info-item').forEach(item => {
            const label = item.querySelector('.info-item-label').textContent;
            const value = item.querySelector('.info-item-value').textContent;
            dataToCopy += `${label}: ${value}\n`;
        });
    } else if (postsContainer.style.display !== 'none') {
        // Copy posts data
        dataToCopy = 'Posts Data\n\n';
        document.querySelectorAll('.post-card').forEach((post, index) => {
            dataToCopy += `Post ${index + 1}:\n`;
            dataToCopy += post.textContent + '\n\n';
        });
    }
    
    if (dataToCopy) {
        navigator.clipboard.writeText(dataToCopy).then(() => {
            showSocialAlert('Data copied to clipboard!', 'success');
        }).catch(() => {
            showSocialAlert('Failed to copy data', 'danger');
        });
    }
}

// ================================================
// Utility Functions
// ================================================

function formatLabel(str) {
    return str
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

function formatValue(value) {
    if (typeof value === 'number') {
        return value.toLocaleString();
    }
    if (typeof value === 'boolean') {
        return value ? '✓ Yes' : '✗ No';
    }
    if (value && typeof value === 'object') {
        return JSON.stringify(value);
    }
    return value;
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length > maxLength) {
        return text.substring(0, maxLength) + '...';
    }
    return text;
}

// ================================================
// Initialize on DOM Load
// ================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeSocialMedia();
});
