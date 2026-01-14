# Diagram Management

This directory contains visual diagrams for the Resume as Code documentation. Diagrams are authored in [Excalidraw](https://excalidraw.com/) format and exported to SVG for display.

---

## Available Diagrams

| File | Description |
|------|-------------|
| `data-model.excalidraw` | Entity relationships showing Work Unit, Position, Certification, Education, Publication, and Board Role models |
| `workflow-pipeline.excalidraw` | The Capture → Validate → Plan → Build pipeline visualization |
| `philosophy-concept.excalidraw` | Traditional resume editing vs Resume as Code comparison |

---

## Editing Diagrams

### Option 1: Excalidraw Web App (Recommended)

1. Go to [excalidraw.com](https://excalidraw.com/)
2. Click **Open** and select the `.excalidraw` file
3. Make your edits
4. Click **Save** to download the updated `.excalidraw` file
5. Replace the file in this directory
6. Run the export script (see below)

### Option 2: VS Code Extension

Install the [Excalidraw VS Code extension](https://marketplace.visualstudio.com/items?itemName=pomdtr.excalidraw-editor) for in-editor editing.

---

## Exporting to SVG

After editing diagrams, export them to SVG using the provided script.

### Prerequisites

The export script requires Node.js (v18+). No additional dependencies are needed — the script uses native SVG generation without browser dependencies.

### Running the Export Script

```bash
# From project root
node scripts/export-excalidraw-svg.mjs
```

### Expected Output

```
Exporting Excalidraw diagrams to SVG...

Found 3 diagrams to export

Converting data-model.excalidraw...
  ✓ Exported to data-model.svg
Converting philosophy-concept.excalidraw...
  ✓ Exported to philosophy-concept.svg
Converting workflow-pipeline.excalidraw...
  ✓ Exported to workflow-pipeline.svg

Done: 3 exported, 0 failed
```

### What the Script Does

1. Scans `docs/diagrams/` for `.excalidraw` files
2. Parses the Excalidraw JSON format
3. Converts elements (rectangles, text, lines, arrows) to native SVG
4. Writes `.svg` files alongside the source `.excalidraw` files

---

## Script Details

**Location**: `scripts/export-excalidraw-svg.mjs`

### Supported Elements

| Excalidraw Element | SVG Output |
|--------------------|------------|
| `rectangle` | `<rect>` with fill, stroke, rounded corners |
| `text` | `<text>` with multi-line support via `<tspan>` |
| `line` | `<path>` with optional dashed/dotted styles |
| `arrow` | `<path>` with arrowhead rendering |

### Font Mapping

| Excalidraw Font | SVG Font Family |
|-----------------|-----------------|
| Hand-drawn (1) | Virgil, serif |
| Normal (2) | Helvetica, sans-serif |
| Code (3) | Cascadia, monospace |

### Limitations

- Complex curved arrows render as straight segments
- Hand-drawn "roughness" style is rendered as clean lines
- Embedded images are not supported

For pixel-perfect exports matching Excalidraw's rendering, use the web app's built-in **Export to SVG** feature instead.

---

## Adding New Diagrams

1. Create your diagram in Excalidraw
2. Save as `<name>.excalidraw` in this directory
3. Run `node scripts/export-excalidraw-svg.mjs`
4. Reference the SVG in documentation:

```markdown
![Diagram Description](./diagrams/<name>.svg)
```

---

## Troubleshooting

### "No .excalidraw files found"

Ensure files have the `.excalidraw` extension (not `.excalidraw.json`).

### SVG looks different from Excalidraw preview

The export script produces clean SVG without hand-drawn effects. For exact visual fidelity, use Excalidraw's built-in export:

1. Open diagram in [excalidraw.com](https://excalidraw.com/)
2. Select all elements (Ctrl+A / Cmd+A)
3. Click **Export image** → **SVG**
4. Save to this directory

### Text positioning issues

Verify the `.excalidraw` file has correct `width` and `height` values for text elements. Re-save from Excalidraw if needed.
