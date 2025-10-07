/**
 * CodeCritique Application JavaScript
 * Main application logic and utilities
 */

// Application state
const AppState = {
    currentReview: null,
    isOnline: navigator.onLine,
    installPrompt: null
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('CodeCritique: Initializing application...');
    
    initializeApp();
    setupEventListeners();
    setupOfflineHandling();
    setupFormValidation();
    setupProgressTracking();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Check if we're in a review session
    const reviewData = sessionStorage.getItem('currentReview');
    if (reviewData) {
        AppState.currentReview = JSON.parse(reviewData);
        updateProgressDisplay();
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Review form submission
    const reviewForms = document.querySelectorAll('form[data-review-form]');
    reviewForms.forEach(form => {
        form.addEventListener('submit', handleReviewSubmission);
    });
    
    // Category navigation
    const categoryNav = document.querySelectorAll('[data-category-nav]');
    categoryNav.forEach(nav => {
        nav.addEventListener('click', handleCategoryNavigation);
    });
    
    // Progress tracking
    const progressInputs = document.querySelectorAll('input[data-progress-track]');
    progressInputs.forEach(input => {
        input.addEventListener('change', handleProgressChange);
    });
    
    // Auto-save functionality
    const autoSaveInputs = document.querySelectorAll('[data-auto-save]');
    autoSaveInputs.forEach(input => {
        input.addEventListener('input', debounce(handleAutoSave, 1000));
    });
}

/**
 * Setup offline handling
 */
function setupOfflineHandling() {
    window.addEventListener('online', function() {
        AppState.isOnline = true;
        showNotification('Connection restored', 'success');
        syncOfflineData();
    });
    
    window.addEventListener('offline', function() {
        AppState.isOnline = false;
        showNotification('You are now offline. Changes will be saved locally.', 'warning');
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Setup progress tracking
 */
function setupProgressTracking() {
    // Calculate initial progress
    updateProgressDisplay();
    
    // Update progress on any change
    document.addEventListener('change', function(event) {
        if (event.target.matches('[data-progress-track]')) {
            updateProgressDisplay();
        }
    });
}

/**
 * Handle review form submission
 */
function handleReviewSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const reviewData = Object.fromEntries(formData.entries());
    
    // Save to session storage
    sessionStorage.setItem('currentReview', JSON.stringify(reviewData));
    AppState.currentReview = reviewData;
    
    // Show success message
    showNotification('Review data saved successfully!', 'success');
    
    // Continue with form submission
    form.submit();
}

/**
 * Handle category navigation
 */
function handleCategoryNavigation(event) {
    event.preventDefault();
    
    const target = event.target.closest('[data-category-nav]');
    const categoryId = target.dataset.categoryId;
    const direction = target.dataset.direction;
    
    if (direction === 'next') {
        navigateToNextCategory(categoryId);
    } else if (direction === 'prev') {
        navigateToPreviousCategory(categoryId);
    }
}

/**
 * Handle progress changes
 */
function handleProgressChange(event) {
    const input = event.target;
    const categoryId = input.dataset.categoryId;
    const itemId = input.dataset.itemId;
    const value = input.value;
    
    // Update progress in session storage
    if (!AppState.currentReview) {
        AppState.currentReview = {};
    }
    
    if (!AppState.currentReview[categoryId]) {
        AppState.currentReview[categoryId] = {};
    }
    
    AppState.currentReview[categoryId][itemId] = value;
    sessionStorage.setItem('currentReview', JSON.stringify(AppState.currentReview));
    
    // Update progress display
    updateProgressDisplay();
}

/**
 * Handle auto-save
 */
function handleAutoSave(event) {
    const input = event.target;
    const data = {
        name: input.name,
        value: input.value,
        timestamp: new Date().toISOString()
    };
    
    // Save to local storage for offline sync
    const autoSaveKey = `autosave_${input.name}`;
    localStorage.setItem(autoSaveKey, JSON.stringify(data));
    
    // Show auto-save indicator
    showAutoSaveIndicator();
}

/**
 * Update progress display
 */
function updateProgressDisplay() {
    const progressBars = document.querySelectorAll('[data-progress-bar]');
    const progressTexts = document.querySelectorAll('[data-progress-text]');
    
    if (progressBars.length === 0) return;
    
    // Calculate progress
    const totalItems = document.querySelectorAll('[data-progress-track]').length;
    const completedItems = document.querySelectorAll('[data-progress-track]:checked').length;
    const progress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
    
    // Update progress bars
    progressBars.forEach(bar => {
        bar.style.width = `${progress}%`;
        bar.setAttribute('aria-valuenow', progress);
    });
    
    // Update progress text
    progressTexts.forEach(text => {
        text.textContent = `${completedItems}/${totalItems} (${progress}%)`;
    });
}

/**
 * Navigate to next category
 */
function navigateToNextCategory(currentCategoryId) {
    const categories = Array.from(document.querySelectorAll('[data-category]'));
    const currentIndex = categories.findIndex(cat => cat.dataset.category === currentCategoryId);
    
    if (currentIndex < categories.length - 1) {
        const nextCategory = categories[currentIndex + 1];
        nextCategory.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Navigate to previous category
 */
function navigateToPreviousCategory(currentCategoryId) {
    const categories = Array.from(document.querySelectorAll('[data-category]'));
    const currentIndex = categories.findIndex(cat => cat.dataset.category === currentCategoryId);
    
    if (currentIndex > 0) {
        const prevCategory = categories[currentIndex - 1];
        prevCategory.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Sync offline data when back online
 */
async function syncOfflineData() {
    if (!AppState.isOnline) return;
    
    try {
        const autoSaveKeys = Object.keys(localStorage).filter(key => key.startsWith('autosave_'));
        
        for (const key of autoSaveKeys) {
            const data = JSON.parse(localStorage.getItem(key));
            
            // Send to server
            const response = await fetch('/api/sync-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                localStorage.removeItem(key);
            }
        }
        
        showNotification('Offline data synced successfully!', 'success');
    } catch (error) {
        console.error('Failed to sync offline data:', error);
        showNotification('Failed to sync offline data', 'error');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Show auto-save indicator
 */
function showAutoSaveIndicator() {
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.style.display = 'block';
        indicator.textContent = 'Saving...';
        
        setTimeout(() => {
            indicator.textContent = 'Saved';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 1000);
        }, 500);
    }
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility functions
 */
const Utils = {
    formatDate: (date) => {
        return new Date(date).toLocaleDateString();
    },
    
    formatTime: (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },
    
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// Export for use in other scripts
window.CodeCritique = {
    AppState,
    Utils,
    showNotification,
    updateProgressDisplay
};


