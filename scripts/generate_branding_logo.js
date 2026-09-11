const fs = require('fs');
const path = require('path');
// Use the @resvg/resvg-js installed in the parent scratch directory
const { Resvg } = require(path.resolve(__dirname, '../../node_modules/@resvg/resvg-js'));

function buildLogoSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
  <defs>
    <clipPath id="squircle-clip">
      <rect x="24" y="24" width="976" height="976" rx="220" />
    </clipPath>

    <linearGradient id="cyan-glow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f5ff"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>

    <linearGradient id="gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>

    <linearGradient id="facet-light" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#475569"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>

    <linearGradient id="facet-mid" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#334155"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>

    <linearGradient id="facet-dark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>

    <linearGradient id="facet-deep" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#080c14"/>
    </linearGradient>

    <filter id="subtle-shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#000000" flood-opacity="0.14" />
    </filter>
  </defs>

  <!-- 1. Luxury White Squircle Container -->
  <rect x="24" y="24" width="976" height="976" rx="220" fill="#ffffff" stroke="#e2e8f0" stroke-width="6" />

  <g clip-path="url(#squircle-clip)">
    <g transform="translate(512, 512)" filter="url(#subtle-shadow)">

      <!-- 2. Massive Hexagonal Architectural Gateway -->
      <polygon points="
        0,-390
        338,-195
        338,195
        0,390
        -338,195
        -338,-195
      " fill="none" stroke="#0f172a" stroke-width="36" stroke-linejoin="round" />

      <polygon points="
        0,-355
        307,-177
        307,177
        0,355
        -307,177
        -307,-177
      " fill="none" stroke="#00f5ff" stroke-width="4" opacity="0.45" stroke-dasharray="16, 12" />

      <!-- 3. The 85% Mass Symmetrical Falcon / Raptor Mascot -->

      <!-- Outer Wing Mantle (Wingspan) -->
      <!-- Left Outer Wing -->
      <polygon points="0,-160 -120,-110 -240,-10 -280,120 -200,100 -120,60 0,120" fill="url(#facet-mid)" />
      <polygon points="-120,-110 -240,-10 -210,60 -120,60" fill="url(#facet-light)" />
      <polygon points="-240,-10 -280,120 -230,130 -200,100" fill="url(#facet-mid)" />

      <!-- Right Outer Wing (Mirror with shadow tones) -->
      <polygon points="0,-160 120,-110 240,-10 280,120 200,100 120,60 0,120" fill="url(#facet-dark)" />
      <polygon points="120,-110 240,-10 210,60 120,60" fill="url(#facet-mid)" />
      <polygon points="240,-10 280,120 230,130 200,100" fill="url(#facet-deep)" />

      <!-- Wing Flight Feathers Tier 2 -->
      <polygon points="-200,100 -230,130 -160,200 -120,130" fill="url(#facet-dark)" />
      <polygon points="200,100 230,130 160,200 120,130" fill="url(#facet-deep)" />

      <!-- Cyan Wing Accent Contours -->
      <path d="M -120,-110 L -240,-10 L -280,120" fill="none" stroke="#00f5ff" stroke-width="4" opacity="0.8" stroke-linejoin="round" />
      <path d="M 120,-110 L 240,-10 L 280,120" fill="none" stroke="#00f5ff" stroke-width="4" opacity="0.8" stroke-linejoin="round" />

      <!-- Breast Armor Plates (Chevron Pattern) -->
      <polygon points="0,-70 -90,-20 -50,60 0,90" fill="url(#facet-light)" />
      <polygon points="0,-70 90,-20 50,60 0,90" fill="url(#facet-dark)" />

      <polygon points="0,90 -50,60 -70,140 0,180" fill="url(#facet-mid)" />
      <polygon points="0,90 50,60 70,140 0,180" fill="url(#facet-deep)" />

      <!-- Center Breast Energy Inset -->
      <polygon points="0,-20 -30,20 0,50 30,20" fill="url(#cyan-glow)" />

      <!-- Head Crest Feathers -->
      <polygon points="0,-280 -45,-210 -15,-200" fill="url(#facet-light)" />
      <polygon points="0,-280 45,-210 15,-200" fill="url(#facet-dark)" />
      <polygon points="-45,-210 -75,-160 -40,-160" fill="url(#facet-mid)" />
      <polygon points="45,-210 75,-160 40,-160" fill="url(#facet-deep)" />

      <!-- Head / Skull Plates -->
      <polygon points="0,-230 -60,-170 0,-130" fill="#f8fafc" />
      <polygon points="0,-230 60,-170 0,-130" fill="#cbd5e1" />

      <!-- Mask / Brow Facets (Obsidian Helmet) -->
      <polygon points="0,-200 -55,-160 -35,-140 0,-150" fill="#0f172a" />
      <polygon points="0,-200 55,-160 35,-140 0,-150" fill="#090d16" />

      <!-- Electric Cyan Raptor Optics (Eyes) -->
      <polygon points="-48,-160 -25,-155 -32,-145 -52,-150" fill="#00f5ff" />
      <circle cx="-38" cy="-153" r="3" fill="#ffffff" />

      <polygon points="48,-160 25,-155 32,-145 52,-150" fill="#00f5ff" />
      <circle cx="38" cy="-153" r="3" fill="#ffffff" />

      <!-- Golden Hooked Beak (Tomium & Tip) -->
      <polygon points="0,-145 -24,-135 0,-70" fill="url(#gold-grad)" />
      <polygon points="0,-145 24,-135 0,-70" fill="#b45309" />
      <polygon points="0,-100 -12,-110 0,-70" fill="#fef08a" opacity="0.6" />

      <!-- 4. Geometric SemVer Release Ring / Hex Seal clutched by Talons -->
      <g transform="translate(0, 240)">
        <!-- Outer Golden Release Hex Ring -->
        <polygon points="
          0,-80
          70,-40
          70,40
          0,80
          -70,40
          -70,-40
        " fill="#0f172a" stroke="url(#gold-grad)" stroke-width="12" stroke-linejoin="round" />

        <!-- Inner Hex Ring Accent -->
        <polygon points="
          0,-55
          48,-28
          48,28
          0,55
          -48,28
          -48,-28
        " fill="none" stroke="#00f5ff" stroke-width="3.5" stroke-dasharray="8,6" />

        <!-- Luminous SemVer Core Diamond -->
        <polygon points="0,-22 22,0 0,22 -22,0" fill="url(#gold-grad)" />
      </g>

      <!-- Razor Talons Grasping the Ring -->
      <!-- Left Talon Claws -->
      <path d="M -45,160 L -50,195 L -62,190" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M -30,165 L -35,205 L -45,200" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M -15,170 L -18,205 L -26,202" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Right Talon Claws -->
      <path d="M 45,160 L 50,195 L 62,190" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M 30,165 L 35,205 L 45,200" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M 15,170 L 18,205 L 26,202" fill="none" stroke="url(#gold-grad)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />

    </g>
  </g>
</svg>`;
}

async function main() {
  const outputDir = path.resolve(__dirname, '../docs/images');
  const svg = buildLogoSvg();
  const svgPath = path.join(outputDir, 'logo.svg');
  const pngPath = path.join(outputDir, 'logo.png');

  fs.writeFileSync(svgPath, svg, 'utf8');
  console.log('✓ Wrote docs/images/logo.svg');

  const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: 1024 } });
  const pngData = resvg.render().asPng();
  fs.writeFileSync(pngPath, pngData);
  console.log('✓ Successfully rendered docs/images/logo.png at 1024x1024 with Resvg');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
