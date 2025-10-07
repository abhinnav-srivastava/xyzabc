// Desktop app specific functionality
document.addEventListener('DOMContentLoaded', () => {
  // Add desktop-specific UI enhancements
  addDesktopEnhancements();
  
  // Handle desktop-specific events
  handleDesktopEvents();
});

function addDesktopEnhancements() {
  // Add desktop indicator to the UI
  const desktopIndicator = document.createElement('div');
  desktopIndicator.id = 'desktop-indicator';
  desktopIndicator.innerHTML = `
    <div class="desktop-badge">
      <i class="bi bi-laptop"></i>
      <span>Desktop App</span>
    </div>
  `;
  desktopIndicator.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
    background: rgba(0, 123, 255, 0.1);
    border: 1px solid rgba(0, 123, 255, 0.3);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    color: #007bff;
    display: flex;
    align-items: center;
    gap: 4px;
  `;
  
  document.body.appendChild(desktopIndicator);
  
  // Add desktop-specific styles
  const desktopStyles = document.createElement('style');
  desktopStyles.textContent = `
    .desktop-badge {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .desktop-badge i {
      font-size: 14px;
    }
    
    /* Desktop-specific UI improvements */
    @media (min-width: 1200px) {
      .container {
        max-width: 1400px;
      }
    }
    
    /* Hide mobile-specific elements in desktop app */
    .mobile-only {
      display: none !important;
    }
    
    /* Desktop app specific enhancements */
    .desktop-enhanced {
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      border-radius: 8px;
    }
  `;
  document.head.appendChild(desktopStyles);
}

function handleDesktopEvents() {
  // Handle external links in desktop app
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (link && link.href && !link.href.startsWith(window.location.origin)) {
      event.preventDefault();
      if (window.electronAPI) {
        window.electronAPI.openExternal(link.href);
      } else {
        window.open(link.href, '_blank');
      }
    }
  });
  
  // Add keyboard shortcuts for desktop app
  document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + N for new review
    if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
      event.preventDefault();
      window.location.href = '/start_review';
    }
    
    // Ctrl/Cmd + G for guidelines
    if ((event.ctrlKey || event.metaKey) && event.key === 'g') {
      event.preventDefault();
      window.location.href = '/guidelines';
    }
    
    // F5 for reload
    if (event.key === 'F5') {
      event.preventDefault();
      window.location.reload();
    }
  });
  
  // Add desktop app info to console
  console.log('🚀 CodeCritique Desktop App');
  console.log('Platform:', window.electronAPI?.platform || 'web');
  console.log('Version:', window.electronAPI?.getAppVersion?.() || 'unknown');
}

// Desktop-specific PWA enhancements
if (window.electronAPI && window.electronAPI.isDesktop) {
  // Override PWA install for desktop app
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    console.log('Desktop app: PWA install prompt disabled');
  });
  
  // Show desktop app specific message
  console.log('📱 Running as desktop application');
}

