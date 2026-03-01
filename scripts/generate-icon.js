#!/usr/bin/env node
/**
 * Generate icon.ico from static/icons/icon.svg for Electron app icon.
 * Run: node scripts/generate-icon.js
 * Requires: npm install sharp sharp-ico (devDependencies)
 */

const path = require('path');
const fs = require('fs');

const rootDir = path.join(__dirname, '..');
const svgPath = path.join(rootDir, 'static', 'icons', 'icon.svg');
const icoPath = path.join(rootDir, 'static', 'icons', 'icon.ico');

if (!fs.existsSync(svgPath)) {
  console.error('icon.svg not found at', svgPath);
  process.exit(1);
}

async function main() {
  let sharp, ico;
  try {
    sharp = require('sharp');
    ico = require('sharp-ico');
  } catch (e) {
    console.error('Missing dependencies. Run: npm install sharp sharp-ico --save-dev');
    process.exit(1);
  }

  // Use 512x512 source for crisp output; sharp-ico will create all standard sizes
  const source = sharp(svgPath).resize(512, 512);
  await ico.sharpsToIco([source], icoPath, { sizes: 'default' });
  console.log('Generated', icoPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
