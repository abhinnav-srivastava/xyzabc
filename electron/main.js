const { app, BrowserWindow, Menu, BrowserView, ipcMain } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');

const PORT = 5000;
const APP_URL = `http://127.0.0.1:${PORT}`;

let backendProcess = null;
let mainWindow = null;

/** Kill any process listening on the given port (e.g. leftover Flask instances). */
function killProcessesOnPort(port) {
  const isWin = process.platform === 'win32';
  try {
    if (isWin) {
      const out = execSync(`netstat -ano | findstr ":${port}" | findstr "LISTENING"`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      }).trim();
      const pids = new Set();
      for (const line of out.split(/\r?\n/)) {
        const m = line.trim().match(/\s+(\d+)\s*$/);
        if (m) pids.add(m[1]);
      }
      for (const pid of pids) {
        try {
          execSync(`taskkill /F /PID ${pid}`, { stdio: 'ignore', shell: true });
        } catch (_) {}
      }
    } else {
      execSync(`lsof -ti:${port} | xargs kill -9 2>/dev/null || true`, { stdio: 'ignore' });
    }
  } catch (_) {
    // No process on port or command failed
  }
}

/** Stop the backend process and its children. */
function stopBackend() {
  if (backendProcess) {
    try {
      const pid = backendProcess.pid;
      if (pid && process.platform === 'win32') {
        execSync(`taskkill /F /T /PID ${pid}`, { stdio: 'ignore', shell: true });
      } else if (pid) {
        backendProcess.kill('SIGKILL');
      }
    } catch (_) {}
    backendProcess = null;
  }
  killProcessesOnPort(PORT);
}

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'Restore app name.exe');
  }
  return null;
}

function startBackend() {
  return new Promise((resolve, reject) => {
    killProcessesOnPort(PORT);
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
      // Development: spawn Python (use development env so default secret is allowed)
      const appPath = path.join(__dirname, '..');
      const pythonCmd = isWin ? 'python' : 'python3';
      const args = ['app.py', '--no-browser', '--port', String(PORT)];
      backendProcess = spawn(pythonCmd, args, {
        cwd: appPath,
        env: { ...process.env, FLASK_ENV: 'development' }
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

    // Fallback: assume ready after 5 seconds
    setTimeout(resolve, 5000);
  });
}

/** Wait for backend to respond on port (retry until ready or timeout). */
function waitForBackend(port, timeoutMs = 15000) {
  const start = Date.now();
  return new Promise((resolve) => {
    const check = () => {
      const http = require('http');
      const req = http.get(`http://127.0.0.1:${port}/`, { timeout: 2000 }, (res) => {
        res.resume();
        resolve(true);
      });
      req.on('error', () => {
        if (Date.now() - start > timeoutMs) resolve(false);
        else setTimeout(check, 300);
      });
    };
    setTimeout(check, 500);
  });
}

function createWindow() {
  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 800,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, '..', 'static', 'icons', 'icon.ico'),
    show: false,
  });

  mainWindow.loadURL(APP_URL);

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    if (errorCode !== -3) {
      console.error('Failed to load app:', errorCode, errorDescription);
    }
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.maximize();
    mainWindow.focus();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

ipcMain.on('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});
ipcMain.on('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) mainWindow.unmaximize();
    else mainWindow.maximize();
  }
});
ipcMain.on('window-close', () => {
  if (mainWindow) mainWindow.close();
});
ipcMain.handle('window-is-maximized', () => {
  return mainWindow ? mainWindow.isMaximized() : false;
});

app.whenReady().then(async () => {
  try {
    await startBackend();
    const ready = await waitForBackend(PORT);
    if (!ready) console.warn('Backend may not be ready; loading anyway.');
    createWindow();
  } catch (err) {
    console.error('Failed to start:', err);
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('window-all-closed', () => {
  app.quit();
});
