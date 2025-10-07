const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // Platform detection
  platform: process.platform,
  
  // App info
  isElectron: true,
  isDesktop: true
});

