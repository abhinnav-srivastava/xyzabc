/**
 * CodeCritique PWA JavaScript
 * Handles PWA installation, updates, and offline functionality
 */

class PWAManager {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.isOnline = navigator.onLine;
    
    this.init();
  }
  
  init() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
    this.setupOnlineStatus();
    this.setupUpdateNotifications();
    this.setupOfflineHandling();
  }
  
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('PWA: Service Worker registered successfully', registration);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification();
              }
            });
          }
        });
        
      } catch (error) {
        console.error('PWA: Service Worker registration failed', error);
      }
    }
  }
  
  setupInstallPrompt() {
    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('PWA: Install prompt triggered');
      e.preventDefault();
      this.deferredPrompt = e;
      
      // Check if user has dismissed the popup recently (within 7 days)
      const dismissedTime = localStorage.getItem('pwa-install-dismissed');
      const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
      
      if (!dismissedTime || parseInt(dismissedTime) < sevenDaysAgo) {
        // Show popup after a short delay to let the page load
        setTimeout(() => {
          this.showInstallButton();
        }, 3000);
      }
    });
    
    // Listen for the appinstalled event
    window.addEventListener('appinstalled', () => {
      console.log('PWA: App installed successfully');
      this.isInstalled = true;
      this.hideInstallButton();
      this.showInstallSuccessMessage();
    });
    
    // Check if app is already installed
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
      console.log('PWA: App is already installed');
      this.isInstalled = true;
    }
  }
  
  setupOnlineStatus() {
    window.addEventListener('online', () => {
      console.log('PWA: App is online');
      this.isOnline = true;
      this.hideOfflineIndicator();
      this.syncOfflineData();
    });
    
    window.addEventListener('offline', () => {
      console.log('PWA: App is offline');
      this.isOnline = false;
      this.showOfflineIndicator();
    });
  }
  
  setupUpdateNotifications() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'UPDATE_AVAILABLE') {
          this.showUpdateNotification();
        }
      });
    }
  }
  
  setupOfflineHandling() {
    // Store form data when offline
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        if (!this.isOnline) {
          e.preventDefault();
          this.storeOfflineData(form);
          this.showOfflineMessage();
        }
      });
    });
  }
  
  async showInstallButton() {
    // Show the PWA install popup
    const popup = document.getElementById('pwa-install-popup');
    if (popup) {
      popup.style.display = 'block';
      
      // Add smooth slide-in animation
      popup.style.transform = 'translateY(100%)';
      popup.style.transition = 'transform 0.3s ease-out';
      
      // Trigger animation
      setTimeout(() => {
        popup.style.transform = 'translateY(0)';
      }, 10);
      
      // Setup popup event listeners
      this.setupPopupEventListeners();
    }
  }
  
  hideInstallButton() {
    const popup = document.getElementById('pwa-install-popup');
    if (popup) {
      popup.style.transform = 'translateY(100%)';
      setTimeout(() => {
        popup.style.display = 'none';
      }, 300);
    }
  }
  
  setupPopupEventListeners() {
    const installBtn = document.getElementById('pwa-install-btn');
    const dismissBtn = document.getElementById('pwa-dismiss-btn');
    const closeBtn = document.getElementById('pwa-close-btn');
    
    if (installBtn) {
      installBtn.addEventListener('click', () => this.installApp());
    }
    
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        this.hideInstallButton();
        // Store dismissal in localStorage to avoid showing again for a while
        localStorage.setItem('pwa-install-dismissed', Date.now().toString());
      });
    }
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.hideInstallButton();
        // Store dismissal in localStorage to avoid showing again for a while
        localStorage.setItem('pwa-install-dismissed', Date.now().toString());
      });
    }
  }
  
  async installApp() {
    if (this.deferredPrompt) {
      try {
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log('PWA: Install prompt outcome', outcome);
        
        if (outcome === 'accepted') {
          console.log('PWA: User accepted the install prompt');
        } else {
          console.log('PWA: User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
        this.hideInstallButton();
      } catch (error) {
        console.error('PWA: Error during install prompt', error);
      }
    } else {
      console.log('PWA: No install prompt available - showing hint');
      this.showInstallHint();
    }
  }
  
  showInstallHint() {
    const hint = document.getElementById('pwa-install-hint');
    if (hint) {
      hint.style.display = 'block';
    }
  }
  
  showInstallFallbackMessage() {
    const fallbackMessage = document.createElement('div');
    fallbackMessage.className = 'alert alert-info position-fixed';
    fallbackMessage.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    fallbackMessage.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i class="bi bi-info-circle me-2"></i>
          <strong>Install App</strong>
          <br><small>Look for the install option in your browser menu</small>
        </div>
        <button class="btn btn-sm btn-outline-primary" onclick="this.parentElement.parentElement.remove()">
          OK
        </button>
      </div>
    `;
    document.body.appendChild(fallbackMessage);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
      if (fallbackMessage.parentNode) {
        fallbackMessage.parentNode.removeChild(fallbackMessage);
      }
    }, 8000);
  }
  
  showOfflineIndicator() {
    let offlineIndicator = document.getElementById('pwa-offline-indicator');
    if (!offlineIndicator) {
      offlineIndicator = document.createElement('div');
      offlineIndicator.id = 'pwa-offline-indicator';
      offlineIndicator.className = 'alert alert-warning position-fixed';
      offlineIndicator.style.cssText = 'top: 20px; left: 50%; transform: translateX(-50%); z-index: 1050; width: 90%; max-width: 500px;';
      offlineIndicator.innerHTML = '<i class="bi bi-wifi-off me-2"></i>You are offline. Some features may be limited.';
      document.body.appendChild(offlineIndicator);
    }
    offlineIndicator.style.display = 'block';
  }
  
  hideOfflineIndicator() {
    const offlineIndicator = document.getElementById('pwa-offline-indicator');
    if (offlineIndicator) {
      offlineIndicator.style.display = 'none';
    }
  }
  
  showUpdateNotification() {
    const updateNotification = document.createElement('div');
    updateNotification.className = 'alert alert-info position-fixed';
    updateNotification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    updateNotification.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i class="bi bi-arrow-clockwise me-2"></i>
          <strong>Update Available</strong>
          <br><small>New version is ready to install</small>
        </div>
        <button class="btn btn-sm btn-outline-primary" onclick="window.location.reload()">
          Update
        </button>
      </div>
    `;
    document.body.appendChild(updateNotification);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (updateNotification.parentNode) {
        updateNotification.parentNode.removeChild(updateNotification);
      }
    }, 10000);
  }
  
  showInstallSuccessMessage() {
    const successMessage = document.createElement('div');
    successMessage.className = 'alert alert-success position-fixed';
    successMessage.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    successMessage.innerHTML = '<i class="bi bi-check-circle me-2"></i><strong>App Installed!</strong> CodeCritique is now available on your device.';
    document.body.appendChild(successMessage);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (successMessage.parentNode) {
        successMessage.parentNode.removeChild(successMessage);
      }
    }, 5000);
  }
  
  showOfflineMessage() {
    const offlineMessage = document.createElement('div');
    offlineMessage.className = 'alert alert-warning position-fixed';
    offlineMessage.style.cssText = 'top: 20px; left: 50%; transform: translateX(-50%); z-index: 1050; max-width: 500px;';
    offlineMessage.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <i class="bi bi-wifi-off me-2"></i>
          <strong>Offline Mode</strong>
          <br><small>Your data will be saved and synced when you're back online</small>
        </div>
        <button class="btn btn-sm btn-outline-warning" onclick="this.parentElement.parentElement.remove()">
          OK
        </button>
      </div>
    `;
    document.body.appendChild(offlineMessage);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
      if (offlineMessage.parentNode) {
        offlineMessage.parentNode.removeChild(offlineMessage);
      }
    }, 8000);
  }
  
  storeOfflineData(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
      data[key] = value;
    }
    
    // Store in localStorage for now (in production, use IndexedDB)
    const offlineData = JSON.parse(localStorage.getItem('offlineData') || '[]');
    offlineData.push({
      timestamp: new Date().toISOString(),
      data: data,
      url: window.location.pathname
    });
    localStorage.setItem('offlineData', JSON.stringify(offlineData));
    
    console.log('PWA: Data stored for offline sync', data);
  }
  
  async syncOfflineData() {
    const offlineData = JSON.parse(localStorage.getItem('offlineData') || '[]');
    if (offlineData.length > 0) {
      try {
        // Send offline data to server
        const response = await fetch('/api/sync-offline-data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(offlineData)
        });
        
        if (response.ok) {
          localStorage.removeItem('offlineData');
          console.log('PWA: Offline data synced successfully');
          this.showSyncSuccessMessage();
        }
      } catch (error) {
        console.error('PWA: Failed to sync offline data', error);
      }
    }
  }
  
  showSyncSuccessMessage() {
    const syncMessage = document.createElement('div');
    syncMessage.className = 'alert alert-success position-fixed';
    syncMessage.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    syncMessage.innerHTML = '<i class="bi bi-cloud-check me-2"></i><strong>Data Synced!</strong> Your offline data has been synchronized.';
    document.body.appendChild(syncMessage);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      if (syncMessage.parentNode) {
        syncMessage.parentNode.removeChild(syncMessage);
      }
    }, 3000);
  }
  
  // Public methods for external use
  async checkForUpdates() {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        registration.update();
      }
    }
  }
  
  async unregisterServiceWorker() {
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(registrations.map(registration => registration.unregister()));
      console.log('PWA: Service Worker unregistered');
    }
  }
}

// Initialize PWA when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.pwaManager = new PWAManager();
});

// Debug function for manual popup testing (only in development)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  window.testPWAPopup = function() {
    console.log('PWA: Manual test triggered');
    if (window.pwaManager) {
      window.pwaManager.showInstallButton();
    } else {
      console.error('PWA: Manager not initialized');
    }
  };
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PWAManager;
}
