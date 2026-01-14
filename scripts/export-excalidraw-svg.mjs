#!/usr/bin/env node
/**
 * Export Excalidraw diagrams to SVG format by directly parsing the JSON.
 * No browser dependencies required.
 *
 * Usage: node scripts/export-excalidraw-svg.mjs
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, basename, resolve } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DIAGRAMS_DIR = resolve(__dirname, '../docs/diagrams');

// Excalidraw fontFamily mapping
const FONT_FAMILIES = {
  1: 'Virgil, Segoe UI Emoji, Apple Color Emoji, serif',  // Hand-drawn
  2: 'Helvetica, sans-serif',
  3: 'Cascadia, monospace',  // Code/monospace
};

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function calculateBounds(elements) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  for (const el of elements) {
    if (el.isDeleted) continue;

    let elMinX = el.x;
    let elMinY = el.y;
    let elMaxX = el.x + (el.width || 0);
    let elMaxY = el.y + (el.height || 0);

    // Handle lines and arrows with points
    if (el.points && el.points.length > 0) {
      for (const point of el.points) {
        elMaxX = Math.max(elMaxX, el.x + point[0]);
        elMaxY = Math.max(elMaxY, el.y + point[1]);
        elMinX = Math.min(elMinX, el.x + point[0]);
        elMinY = Math.min(elMinY, el.y + point[1]);
      }
    }

    minX = Math.min(minX, elMinX);
    minY = Math.min(minY, elMinY);
    maxX = Math.max(maxX, elMaxX);
    maxY = Math.max(maxY, elMaxY);
  }

  const padding = 40;
  return {
    x: minX - padding,
    y: minY - padding,
    width: maxX - minX + padding * 2,
    height: maxY - minY + padding * 2,
  };
}

function renderRectangle(el, offsetX, offsetY) {
  const x = el.x - offsetX;
  const y = el.y - offsetY;
  const fill = el.backgroundColor === 'transparent' ? 'none' : el.backgroundColor;
  const strokeDasharray = el.strokeStyle === 'dashed' ? '8,4' :
                          el.strokeStyle === 'dotted' ? '2,2' : 'none';
  const rx = el.roundness ? 8 : 0;

  return `  <rect x="${x}" y="${y}" width="${el.width}" height="${el.height}"
    fill="${fill}" stroke="${el.strokeColor}" stroke-width="${el.strokeWidth}"
    ${strokeDasharray !== 'none' ? `stroke-dasharray="${strokeDasharray}"` : ''}
    rx="${rx}" ry="${rx}" opacity="${el.opacity / 100}" />`;
}

function renderText(el, offsetX, offsetY) {
  const x = el.x - offsetX;
  const y = el.y - offsetY;
  const fontFamily = FONT_FAMILIES[el.fontFamily] || FONT_FAMILIES[1];
  const lines = (el.text || '').split('\n');
  const lineHeight = el.fontSize * (el.lineHeight || 1.25);

  let textAnchor = 'start';
  let adjustedX = x;
  if (el.textAlign === 'center') {
    textAnchor = 'middle';
    adjustedX = x + (el.width || 0) / 2;
  } else if (el.textAlign === 'right') {
    textAnchor = 'end';
    adjustedX = x + (el.width || 0);
  }

  const textElements = lines.map((line, i) => {
    const lineY = y + el.fontSize + i * lineHeight;
    return `    <tspan x="${adjustedX}" y="${lineY}">${escapeXml(line)}</tspan>`;
  }).join('\n');

  return `  <text x="${adjustedX}" y="${y}" font-family="${fontFamily}" font-size="${el.fontSize}"
    fill="${el.strokeColor}" text-anchor="${textAnchor}" opacity="${el.opacity / 100}">
${textElements}
  </text>`;
}

function renderLine(el, offsetX, offsetY) {
  if (!el.points || el.points.length < 2) return '';

  const startX = el.x - offsetX;
  const startY = el.y - offsetY;
  const strokeDasharray = el.strokeStyle === 'dashed' ? '8,4' :
                          el.strokeStyle === 'dotted' ? '2,2' : 'none';

  const pathParts = el.points.map((point, i) => {
    const cmd = i === 0 ? 'M' : 'L';
    return `${cmd}${startX + point[0]},${startY + point[1]}`;
  });

  return `  <path d="${pathParts.join(' ')}" fill="none" stroke="${el.strokeColor}"
    stroke-width="${el.strokeWidth}" ${strokeDasharray !== 'none' ? `stroke-dasharray="${strokeDasharray}"` : ''}
    opacity="${el.opacity / 100}" />`;
}

function renderArrow(el, offsetX, offsetY) {
  if (!el.points || el.points.length < 2) return '';

  const startX = el.x - offsetX;
  const startY = el.y - offsetY;

  const pathParts = el.points.map((point, i) => {
    const cmd = i === 0 ? 'M' : 'L';
    return `${cmd}${startX + point[0]},${startY + point[1]}`;
  });

  // Get end point for arrowhead
  const lastPoint = el.points[el.points.length - 1];
  const prevPoint = el.points[el.points.length - 2] || [0, 0];
  const endX = startX + lastPoint[0];
  const endY = startY + lastPoint[1];

  // Calculate arrow angle
  const dx = lastPoint[0] - prevPoint[0];
  const dy = lastPoint[1] - prevPoint[1];
  const angle = Math.atan2(dy, dx);

  // Arrow head size
  const arrowSize = 10;
  const arrowAngle = Math.PI / 6;

  let arrowHead = '';
  if (el.endArrowhead === 'arrow') {
    const x1 = endX - arrowSize * Math.cos(angle - arrowAngle);
    const y1 = endY - arrowSize * Math.sin(angle - arrowAngle);
    const x2 = endX - arrowSize * Math.cos(angle + arrowAngle);
    const y2 = endY - arrowSize * Math.sin(angle + arrowAngle);
    arrowHead = `  <path d="M${x1},${y1} L${endX},${endY} L${x2},${y2}"
    fill="none" stroke="${el.strokeColor}" stroke-width="${el.strokeWidth}" />`;
  }

  return `  <path d="${pathParts.join(' ')}" fill="none" stroke="${el.strokeColor}"
    stroke-width="${el.strokeWidth}" opacity="${el.opacity / 100}" />
${arrowHead}`;
}

function convertToSvg(data) {
  const elements = data.elements.filter(el => !el.isDeleted);
  const bounds = calculateBounds(elements);
  const bgColor = data.appState?.viewBackgroundColor || '#ffffff';

  // Sort elements by index for proper layering
  const sortedElements = [...elements].sort((a, b) => {
    const indexA = a.index || '';
    const indexB = b.index || '';
    return indexA.localeCompare(indexB);
  });

  const svgParts = [];

  // Background
  svgParts.push(`  <rect x="0" y="0" width="${bounds.width}" height="${bounds.height}" fill="${bgColor}" />`);

  // Render elements
  for (const el of sortedElements) {
    switch (el.type) {
      case 'rectangle':
        svgParts.push(renderRectangle(el, bounds.x, bounds.y));
        break;
      case 'text':
        svgParts.push(renderText(el, bounds.x, bounds.y));
        break;
      case 'line':
        svgParts.push(renderLine(el, bounds.x, bounds.y));
        break;
      case 'arrow':
        svgParts.push(renderArrow(el, bounds.x, bounds.y));
        break;
    }
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 ${bounds.width} ${bounds.height}"
     width="${bounds.width}" height="${bounds.height}">
${svgParts.join('\n')}
</svg>`;
}

function main() {
  console.log('Exporting Excalidraw diagrams to SVG...\n');

  const files = readdirSync(DIAGRAMS_DIR)
    .filter(f => f.endsWith('.excalidraw'))
    .map(f => join(DIAGRAMS_DIR, f));

  if (files.length === 0) {
    console.log('No .excalidraw files found in', DIAGRAMS_DIR);
    return;
  }

  console.log(`Found ${files.length} diagrams to export\n`);

  let success = 0;
  let failed = 0;

  for (const inputPath of files) {
    const outputPath = inputPath.replace('.excalidraw', '.svg');
    const filename = basename(inputPath);

    console.log(`Converting ${filename}...`);

    try {
      const fileContent = readFileSync(inputPath, 'utf-8');
      const data = JSON.parse(fileContent);
      const svgString = convertToSvg(data);

      writeFileSync(outputPath, svgString);
      console.log(`  ✓ Exported to ${basename(outputPath)}`);
      success++;
    } catch (error) {
      console.error(`  ✗ Failed: ${error.message}`);
      failed++;
    }
  }

  console.log(`\nDone: ${success} exported, ${failed} failed`);
}

main();
