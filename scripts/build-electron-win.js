#!/usr/bin/env node
/**
 * Build CodeReview as a fully bundled Windows desktop app.
 * 1. PyInstaller bundles Flask + Python + deps into CodeReview.exe
 * 2. Electron wraps it - no Python/Flask required on target machine
 *
 * Prerequisites: Node.js, npm, Python (for build only)
 * Run: npm run build:win   or   node scripts/build-electron-win.js
 */

const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.join(__dirname, '..');

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

function runPy(args) {
  console.log('>', 'python', args.join(' '));
  const r = spawnSync('python', args, { stdio: 'inherit', cwd: rootDir });
  if (r.status !== 0) throw new Error(`python ${args.join(' ')} failed`);
}

function main() {
  console.log('Building CodeReview for Windows (fully bundled)...\n');

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
    console.error('app.spec not found.');
    process.exit(1);
  }
  const exeName = getExeNameFromSpec();
  runPy(['-m', 'PyInstaller', '--clean', '--noconfirm', 'app.spec']);

  const exePath = path.join(rootDir, 'dist', `${exeName}.exe`);
  if (!fs.existsSync(exePath)) {
    console.error(`PyInstaller did not produce dist/${exeName}.exe`);
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

  // 2. Install npm deps if needed
  if (!fs.existsSync(path.join(rootDir, 'node_modules'))) {
    console.log('Step 2: Installing npm dependencies...');
    run('npm install');
  } else {
    console.log('Step 2: npm deps already installed');
  }

  // 3. Electron-builder: use timestamped output to avoid "file in use" from previous runs
  const outDir = `dist-electron-${Date.now()}`;
  console.log('\nStep 3: Packaging with Electron...');
  run(`npx electron-builder --win --config.directories.output=${outDir} --config.win.signAndEditExecutable=false`);

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
