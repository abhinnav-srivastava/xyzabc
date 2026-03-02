#!/usr/bin/env node
/**
 * Build CodeReview as a fully bundled Windows desktop app.
 * 1. PyInstaller bundles Flask + Python + deps into CodeReview.exe
 * 2. Electron wraps it - no Python/Flask required on target machine
 *
 * Prerequisites: Node.js, npm, Python (for build only)
 * Run: npm run build:win   or   node scripts/build-electron-win.js
 *
 * Resilience: pre-checks, retries for network ops, graceful fallback on Electron failure.
 */

const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const rootDir = path.join(__dirname, '..');

const ELECTRON_BUILDER_MAX_RETRIES = 3;
const RETRY_DELAY_MS = 5000;

/** Check Node.js version (18+ recommended for Electron) */
function checkNodeVersion() {
  const v = process.version;
  const major = parseInt(v.slice(1).split('.')[0], 10);
  if (major < 16) {
    console.warn(`WARN: Node ${v} may cause issues. Node 18+ recommended.`);
  }
  return major >= 16;
}

/** Ensure npm deps exist; run npm install if electron or electron-builder missing */
function ensureNpmDeps() {
  const electronPath = path.join(rootDir, 'node_modules', 'electron');
  const builderPath = path.join(rootDir, 'node_modules', 'electron-builder');
  if (!fs.existsSync(electronPath) || !fs.existsSync(builderPath)) {
    console.log('  electron/electron-builder missing - running npm install...');
    return false;
  }
  return true;
}

/** Find a working Python executable (python, python3, py -3 on Windows) */
function findPython() {
  const candidates = process.platform === 'win32'
    ? ['python', 'py -3', 'python3']
    : ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      const r = spawnSync(cmd, ['-c', 'import sys; print(sys.executable)'], {
        encoding: 'utf8',
        cwd: rootDir,
        shell: cmd.includes(' ')
      });
      if (r.status === 0 && r.stdout && r.stdout.trim()) {
        return cmd;
      }
    } catch (_) {}
  }
  return null;
}

/** Parse exe name from app.spec (e.g. name='CodeReview' or name='CodeCrit') */
function getExeNameFromSpec() {
  const specPath = path.join(rootDir, 'app.spec');
  const content = fs.readFileSync(specPath, 'utf8');
  const m = content.match(/exe\s*=\s*EXE\s*\([\s\S]*?name\s*=\s*['"]([^'"]+)['"]/);
  if (m) return m[1];
  const fallback = content.match(/name\s*=\s*['"]([^'"]+)['"]/);
  return fallback ? fallback[1] : 'CodeReview';
}

function run(cmd, opts = {}) {
  console.log('>', cmd);
  return execSync(cmd, { stdio: 'inherit', cwd: rootDir, ...opts });
}

function runPy(pythonCmd, args) {
  console.log('>', pythonCmd, args.join(' '));
  const r = spawnSync(pythonCmd, args, {
    stdio: 'inherit',
    cwd: rootDir,
    shell: pythonCmd.includes(' ')
  });
  if (r.status !== 0) throw new Error(`Python command failed with code ${r.status}`);
}

function main() {
  const skipElectron = process.argv.includes('--skip-electron');
  if (skipElectron) {
    console.log('Building CodeReview (PyInstaller only, skipping Electron)...\n');
  } else {
    console.log('Building CodeReview for Windows (fully bundled)...\n');
  }

  // Resolve Python
  const pythonCmd = findPython();
  if (!pythonCmd) {
    console.error('ERROR: Python not found. Tried: python, python3, py -3 (Windows)');
    console.error('  Install Python 3.9+ from https://www.python.org/');
    process.exit(1);
  }
  console.log('Using Python:', pythonCmd);

  // 0. Generate app icon if missing
  const icoPath = path.join(rootDir, 'static', 'icons', 'icon.ico');
  if (!fs.existsSync(icoPath)) {
    console.log('Step 0: Generating app icon...');
    try {
      execSync('node scripts/generate-icon.js', { stdio: 'inherit', cwd: rootDir });
    } catch (e) {
      console.warn('  (Icon generation skipped - run "npm run generate-icon" manually)');
    }
  }

  // 1. PyInstaller: bundle Flask app
  console.log('Step 1: Bundling Flask backend with PyInstaller...');
  const specPath = path.join(rootDir, 'app.spec');
  if (!fs.existsSync(specPath)) {
    console.error('ERROR: app.spec not found.');
    process.exit(1);
  }
  const exeName = getExeNameFromSpec();
  try {
    runPy(pythonCmd, ['-m', 'PyInstaller', '--clean', '--noconfirm', 'app.spec']);
  } catch (e) {
    console.error('PyInstaller failed. Common causes:');
    console.error('  - Python 3.9+ required; run: pip install -r requirements.txt');
    console.error('  - Antivirus may block PyInstaller; add project folder to exclusions');
    console.error('  - Long paths: enable in Windows or shorten project path');
    process.exit(1);
  }

  const exePath = path.join(rootDir, 'dist', `${exeName}.exe`);
  if (!fs.existsSync(exePath)) {
    console.error(`ERROR: PyInstaller did not produce dist/${exeName}.exe`);
    process.exit(1);
  }
  console.log(`  -> dist/${exeName}.exe created`);

  // Ensure dist/CodeReview.exe exists for electron-builder (package.json + main.js expect it)
  const electronExePath = path.join(rootDir, 'dist', 'CodeReview.exe');
  if (exeName !== 'CodeReview') {
    fs.copyFileSync(exePath, electronExePath);
    console.log(`  -> copied to dist/CodeReview.exe for Electron\n`);
  } else {
    console.log('\n');
  }

  if (skipElectron) {
    console.log('Skipping Electron (--skip-electron). dist/CodeReview.exe is ready.');
    console.log('Run "npm run build:win" without --skip-electron when Electron is available.');
    return;
  }

  // 2. Install npm deps if needed
  const needsNpmInstall = !fs.existsSync(path.join(rootDir, 'node_modules')) || !ensureNpmDeps();
  try {
    if (needsNpmInstall) {
      console.log('Step 2: Installing npm dependencies...');
      run('npm install');
    } else {
      console.log('Step 2: npm deps already installed');
    }
  } catch (e) {
    console.error('npm install failed. Run "npm install" manually and retry.');
    console.error('Or run with --skip-electron to build only the PyInstaller exe.');
    process.exit(1);
  }

  // 3. Electron-builder: use timestamped output to avoid "file in use" from previous runs
  const outDir = `dist-electron-${Date.now()}`;
  console.log('\nStep 3: Packaging with Electron...');
  checkNodeVersion();

  const electronBuilderCmd = `npx electron-builder --win --config.directories.output=${outDir} --config.win.signAndEditExecutable=false`;
  for (let attempt = 1; attempt <= ELECTRON_BUILDER_MAX_RETRIES; attempt++) {
    try {
      if (attempt > 1) {
        console.log(`  Retry ${attempt}/${ELECTRON_BUILDER_MAX_RETRIES} (waiting ${RETRY_DELAY_MS / 1000}s)...`);
        const sleepSec = Math.ceil(RETRY_DELAY_MS / 1000);
        const sleepCmd = process.platform === 'win32'
          ? `ping -n ${sleepSec + 1} 127.0.0.1 >nul`
          : `sleep ${sleepSec}`;
        try {
          execSync(sleepCmd, { stdio: 'ignore', cwd: rootDir });
        } catch (_) {
          // sleep failed; continue anyway
        }
      }
      run(electronBuilderCmd);
      break;
    } catch (e) {
      const isLast = attempt === ELECTRON_BUILDER_MAX_RETRIES;
      console.error(`  Attempt ${attempt}/${ELECTRON_BUILDER_MAX_RETRIES} failed.`);
      if (isLast) {
        console.error('Electron-builder failed after retries. Common causes:');
        console.error('  - Network/proxy: set HTTPS_PROXY, HTTP_PROXY if behind firewall');
        console.error('  - Disk space: ensure enough free space for Electron binaries');
        console.error('  - Node 18+ recommended; run: node -v');
        console.error('  - Try: npm cache clean --force && npm install');
        console.error('');
        console.error('PyInstaller step succeeded. You have dist/CodeReview.exe.');
        console.error('Options:');
        console.error('  1. Run "npm run build:win -- --skip-electron" to skip Electron next time');
        console.error('  2. Run "npm run build:win" again later (e.g. after fixing network)');
        console.error('  3. Use "npx electron ." from project root with dist/CodeReview.exe present');
        process.exit(1);
      }
    }
  }

  // 4. Create portable zip (copy folder, unzip anywhere, run)
  const distDir = path.join(rootDir, outDir);
  const winDirPath = path.join(distDir, 'win-unpacked');
  const pkg = JSON.parse(fs.readFileSync(path.join(rootDir, 'package.json'), 'utf8'));
  const productName = pkg.build?.productName || exeName || 'CodeReview';
  if (fs.existsSync(winDirPath)) {
    console.log('\nStep 4: Creating portable zip...');
    const zipPath = path.join(distDir, `${productName}-portable.zip`);
    const winContents = path.join(winDirPath, '*');
    try {
      execSync(
        `powershell -NoProfile -Command "Compress-Archive -Path '${winContents}' -DestinationPath '${zipPath}' -Force"`,
        { stdio: 'inherit', cwd: rootDir }
      );
      console.log(`  -> ${productName}-portable.zip created`);
    } catch (e) {
      console.warn('  (Zip creation skipped - PowerShell may be unavailable)');
    }
    console.log(`\nDone! Artifacts in ${outDir}/:`);
    console.log(`  - ${productName} X.X.X.exe (portable) - copy & run, no install`);
    console.log(`  - ${productName}-portable.zip - unzip anywhere, run ${productName}.exe`);
  } else {
    console.log(`\nDone! Output in ${outDir}/`);
  }
}

main();
