const { app, BrowserWindow, Menu, BrowserView } = require('electron');
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
    return path.join(process.resourcesPath, 'backend', 'CodeReview.exe');
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
  Menu.setApplicationMenu(null);

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

  const progressBar = new BrowserView({
    webPreferences: { nodeIntegration: false },
  });
  mainWindow.setBrowserView(progressBar);
  progressBar.setBounds({ x: 0, y: 0, width: 1280, height: 5 });
  progressBar.webContents.loadURL(
    'data:text/html;charset=utf-8,' + encodeURIComponent(`
      <!DOCTYPE html><html><head><style>
        *{margin:0}body{height:5px;background:#e9ecef;overflow:hidden}
        body::after{content:'';display:block;height:100%;width:30%;background:linear-gradient(90deg,#0d6efd,#0a58ca);
          animation:l 1.2s ease-in-out infinite}
        @keyframes l{0%{transform:translateX(-100%)}100%{transform:translateX(400%)}}
      </style></head><body></body></html>`
    )
  );

  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.setBrowserView(null);
  });

  mainWindow.on('resize', () => {
    const [w, h] = mainWindow.getContentSize();
    if (mainWindow.getBrowserView()) {
      mainWindow.getBrowserView().setBounds({ x: 0, y: 0, width: w, height: 5 });
    }
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

app.on('before-quit', () => {
  stopBackend();
});

app.on('window-all-closed', () => {
  app.quit();
});
