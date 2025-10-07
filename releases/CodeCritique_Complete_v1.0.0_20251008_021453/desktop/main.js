const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow;
let flaskProcess;

// Configuration
const CONFIG = {
  flaskPort: 5000,
  flaskHost: '127.0.0.1',
  appUrl: `http://127.0.0.1:5000`,
  windowTitle: 'CodeCritique - Professional Code Review Tool',
  windowWidth: 1200,
  windowHeight: 800,
  minWidth: 800,
  minHeight: 600
};

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: CONFIG.windowWidth,
    height: CONFIG.windowHeight,
    minWidth: CONFIG.minWidth,
    minHeight: CONFIG.minHeight,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: CONFIG.windowTitle,
    show: false, // Don't show until ready
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
  });

  // Create application menu
  createMenu();

  // Start Flask server
  startFlaskServer();

  // Load the app when Flask is ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus on the window
    if (mainWindow) {
      mainWindow.focus();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    stopFlaskServer();
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Prevent navigation to external URLs
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.origin !== CONFIG.appUrl) {
      event.preventDefault();
      shell.openExternal(navigationUrl);
    }
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Review',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            if (mainWindow) {
              mainWindow.loadURL(`${CONFIG.appUrl}/start_review`);
            }
          }
        },
        {
          label: 'Open Guidelines',
          accelerator: 'CmdOrCtrl+G',
          click: () => {
            if (mainWindow) {
              mainWindow.loadURL(`${CONFIG.appUrl}/guidelines`);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            if (mainWindow) {
              mainWindow.reload();
            }
          }
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.toggleDevTools();
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Actual Size',
          accelerator: 'CmdOrCtrl+0',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.setZoomLevel(0);
            }
          }
        },
        {
          label: 'Zoom In',
          accelerator: 'CmdOrCtrl+Plus',
          click: () => {
            if (mainWindow) {
              const currentZoom = mainWindow.webContents.getZoomLevel();
              mainWindow.webContents.setZoomLevel(currentZoom + 0.5);
            }
          }
        },
        {
          label: 'Zoom Out',
          accelerator: 'CmdOrCtrl+-',
          click: () => {
            if (mainWindow) {
              const currentZoom = mainWindow.webContents.getZoomLevel();
              mainWindow.webContents.setZoomLevel(currentZoom - 0.5);
            }
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About CodeCritique',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About CodeCritique',
              message: 'CodeCritique Desktop',
              detail: 'Professional code review tool with role-based, category-driven checklists.\n\nVersion 1.0.0\nLicensed under Apache 2.0'
            });
          }
        },
        {
          label: 'Open in Browser',
          click: () => {
            shell.openExternal(CONFIG.appUrl);
          }
        }
      ]
    }
  ];

  // macOS specific menu adjustments
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        {
          label: 'About ' + app.getName(),
          role: 'about'
        },
        { type: 'separator' },
        {
          label: 'Services',
          role: 'services',
          submenu: []
        },
        { type: 'separator' },
        {
          label: 'Hide ' + app.getName(),
          accelerator: 'Command+H',
          role: 'hide'
        },
        {
          label: 'Hide Others',
          accelerator: 'Command+Shift+H',
          role: 'hideothers'
        },
        {
          label: 'Show All',
          role: 'unhide'
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'Command+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function startFlaskServer() {
  console.log('Starting Flask server...');
  
  // Look for the executable in the same directory as the Electron app
  const executablePath = path.join(__dirname, '..', 'dist', 'CodeCritique.exe');
  
  if (!fs.existsSync(executablePath)) {
    console.error('Flask executable not found:', executablePath);
    dialog.showErrorBox(
      'Flask Server Not Found',
      'The CodeCritique executable was not found. Please ensure the application is properly built.'
    );
    return;
  }

  // Start Flask process
  flaskProcess = spawn(executablePath, [], {
    cwd: path.dirname(executablePath),
    stdio: ['pipe', 'pipe', 'pipe']
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log('Flask:', data.toString());
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error('Flask Error:', data.toString());
  });

  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
  });

  flaskProcess.on('error', (err) => {
    console.error('Failed to start Flask process:', err);
    dialog.showErrorBox(
      'Server Error',
      'Failed to start the CodeCritique server. Please check the console for details.'
    );
  });

  // Wait for Flask to start, then load the app
  setTimeout(() => {
    if (mainWindow) {
      mainWindow.loadURL(CONFIG.appUrl);
    }
  }, 3000); // Wait 3 seconds for Flask to start
}

function stopFlaskServer() {
  if (flaskProcess) {
    console.log('Stopping Flask server...');
    flaskProcess.kill();
    flaskProcess = null;
  }
}

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopFlaskServer();
});

// Handle app protocol for deep linking (optional)
app.setAsDefaultProtocolClient('codecritique');

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('open-external', (event, url) => {
  shell.openExternal(url);
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

