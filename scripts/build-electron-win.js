#!/usr/bin/env node
/**
 * Build CodeCritique as a fully bundled Windows desktop app.
 * 1. PyInstaller bundles Flask + Python + deps into CodeCritique.exe
 * 2. Electron wraps it - no Python/Flask required on target machine
 *
 * Prerequisites: Node.js, npm, Python (for build only)
 * Run: npm run build:win   or   node scripts/build-electron-win.js
 */

const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.join(__dirname, '..');

function run(cmd, opts = {}) {
  console.log('>', cmd);
  return execSync(cmd, { stdio: 'inherit', cwd: rootDir, ...opts });
}

function runPy(args) {
  console.log('>', 'python', args.join(' '));
  const r = spawnSync('python', args, { stdio: 'inherit', cwd: rootDir });
  if (r.status !== 0) throw new Error(`python ${args.join(' ')} failed`);
}

function main() {
  console.log('Building CodeCritique for Windows (fully bundled)...\n');

  // 1. PyInstaller: bundle Flask app
  console.log('Step 1: Bundling Flask backend with PyInstaller...');
  const specPath = path.join(rootDir, 'app.spec');
  if (!fs.existsSync(specPath)) {
    console.error('app.spec not found.');
    process.exit(1);
  }
  runPy(['-m', 'PyInstaller', '--clean', '--noconfirm', 'app.spec']);

  const exePath = path.join(rootDir, 'dist', 'CodeCritique.exe');
  if (!fs.existsSync(exePath)) {
    console.error('PyInstaller did not produce dist/CodeCritique.exe');
    process.exit(1);
  }
  console.log('  -> dist/CodeCritique.exe created\n');

  // 2. Install npm deps if needed
  if (!fs.existsSync(path.join(rootDir, 'node_modules'))) {
    console.log('Step 2: Installing npm dependencies...');
    run('npm install');
  } else {
    console.log('Step 2: npm deps already installed');
  }

  // 3. Clean old unpacked dir (avoid "file in use" if app was running)
  const winDir = path.join(rootDir, 'dist-electron', 'win-unpacked');
  if (fs.existsSync(winDir)) {
    console.log('\nStep 3a: Cleaning previous build...');
    try {
      fs.rmSync(winDir, { recursive: true, maxRetries: 3 });
    } catch (e) {
      console.warn('  (Could not remove win-unpacked - close CodeCritique if running)');
    }
  }

  // 4. Electron-builder (portable + unpacked dir)
  console.log('\nStep 4: Packaging with Electron...');
  run('npx electron-builder --win');

  // 5. Create portable zip (copy folder, unzip anywhere, run)
  const distDir = path.join(rootDir, 'dist-electron');
  const winDirPath = path.join(distDir, 'win-unpacked');
  if (fs.existsSync(winDirPath)) {
    console.log('\nStep 5: Creating portable zip...');
    const zipPath = path.join(distDir, 'CodeCritique-portable.zip');
    const winContents = path.join(winDirPath, '*');
    try {
      execSync(
        `powershell -NoProfile -Command "Compress-Archive -Path '${winContents}' -DestinationPath '${zipPath}' -Force"`,
        { stdio: 'inherit', cwd: rootDir }
      );
      console.log('  -> CodeCritique-portable.zip created');
    } catch (e) {
      console.warn('  (Zip creation skipped - PowerShell may be unavailable)');
    }
    console.log('\nDone! Artifacts in dist-electron/:');
    console.log('  - CodeCritique X.X.X.exe (portable) - copy & run, no install');
    console.log('  - CodeCritique-portable.zip - unzip anywhere, run CodeCritique.exe');
  } else {
    console.log('\nDone! Output in dist-electron/');
  }
}

main();
