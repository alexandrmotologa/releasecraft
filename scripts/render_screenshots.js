const fs = require('fs');
const path = require('path');
function loadResvg() {
  const candidatePaths = [
    path.resolve(__dirname, '../../node_modules/@resvg/resvg-js'),
    path.resolve(__dirname, '../node_modules/@resvg/resvg-js'),
    '@resvg/resvg-js',
    'C:/Users/alexander/.gemini/antigravity-ide/brain/911f2964-52f7-4a09-81cb-33cea93c56bc/scratch/node_modules/@resvg/resvg-js',
  ];

  for (const candidate of candidatePaths) {
    try {
      const mod = require(candidate);
      return mod.Resvg || mod;
    } catch {
      // try next
    }
  }
  throw new Error('Could not find @resvg/resvg-js in any candidate path.');
}

const Resvg = loadResvg();

const images = [
  { svg: 'tui_screenshot.svg', png: 'tui_screenshot.png', width: 1600 },
  { svg: 'cli_preview.svg', png: 'cli_preview.png', width: 1400 },
  { svg: 'cli_check.svg', png: 'cli_check.png', width: 1400 },
];

const docsImagesDir = path.resolve(__dirname, '../docs/images');

for (const item of images) {
  const svgPath = path.join(docsImagesDir, item.svg);
  const pngPath = path.join(docsImagesDir, item.png);

  if (!fs.existsSync(svgPath)) {
    console.warn(`[WARN] Skipping missing file: ${svgPath}`);
    continue;
  }

  const svgContent = fs.readFileSync(svgPath, 'utf-8');
  const resvg = new Resvg(svgContent, {
    fitTo: {
      mode: 'width',
      value: item.width,
    },
    background: '#090d16',
    font: {
      loadSystemFonts: true,
      defaultFontFamily: 'Consolas',
    },
  });

  const pngData = resvg.render();
  fs.writeFileSync(pngPath, pngData.asPng());
  console.log(`✓ Successfully rendered ${item.png} (${item.width}px wide)`);
}
