const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 5000;
const APP_URL = `http://127.0.0.1:${PORT}`;

let backendProcess = null;
let mainWindow = null;

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'CodeCritique.exe');
  }
  return null;
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const backendPath = getBackendPath();
    const isWin = process.platform === 'win32';

    if (backendPath) {
      // Packaged: spawn bundled PyInstaller exe
      const args = ['--no-browser', '--port', String(PORT)];
      backendProcess = spawn(backendPath, args, {
        cwd: path.dirname(backendPath),
        env: { ...process.env, FLASK_ENV: 'production' }
      });
    } else {
      // Development: spawn Python
      const appPath = path.join(__dirname, '..');
      const pythonCmd = isWin ? 'python' : 'python3';
      const args = ['app.py', '--no-browser', '--port', String(PORT)];
      backendProcess = spawn(pythonCmd, args, {
        cwd: appPath,
        env: { ...process.env, FLASK_ENV: 'production' }
      });
    }

    backendProcess.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) console.log('[Backend]', msg);
      if (msg.includes('Starting') || msg.includes('Serving')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg && !msg.includes('WARNING')) console.error('[Backend]', msg);
    });

    backendProcess.on('error', (err) => {
      reject(err);
    });

    // Fallback: assume ready after 3 seconds
    setTimeout(resolve, 3000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, '..', 'static', 'icons', 'icon.ico'),
    show: false,
  });

  mainWindow.loadURL(APP_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  try {
    await startBackend();
    createWindow();
  } catch (err) {
    console.error('Failed to start:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  app.quit();
});
