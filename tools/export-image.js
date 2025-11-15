#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const key = arg.replace(/^--/, '');
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        out[key] = next;
        i++;
      } else {
        out[key] = true;
      }
    }
  }
  return out;
}

(async () => {
  try {
    const args = parseArgs(process.argv.slice(2));
    const projectRoot = process.cwd();

    const input = args.input || path.join(projectRoot, 'assets', '5u-hero.svg');
    const output = args.output || path.join(projectRoot, 'assets', '5u-hero-4k.png');
    const width = args.width ? parseInt(args.width, 10) : 3840;
    const height = args.height ? parseInt(args.height, 10) : 2160;

    if (!fs.existsSync(input)) {
      throw new Error(`Input SVG not found: ${input}`);
    }

    await fs.promises.mkdir(path.dirname(output), { recursive: true });

    const svgBuffer = await fs.promises.readFile(input);

    // Render SVG to the requested dimensions
    const image = sharp(svgBuffer)
      .resize({ width, height, fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 1 } })
      .png({ compressionLevel: 9 });

    await image.toFile(output);

    console.log(`Exported PNG: ${output} (${width}x${height})`);
  } catch (err) {
    console.error('Export failed:', err.message);
    process.exit(1);
  }
})();
