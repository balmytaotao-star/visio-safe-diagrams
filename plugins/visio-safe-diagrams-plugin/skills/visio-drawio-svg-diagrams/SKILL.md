---
name: visio-drawio-svg-diagrams
description: Create, repair, and validate Visio-compatible architecture diagrams using draw.io (.drawio) and SVG. Use when Codex needs to generate diagrams for import into Microsoft Visio, fix draw.io atob/base64 errors, prevent SVG text overflow, convert draw.io XML into stable SVG, or troubleshoot diagrams that another agent generated but Visio/draw.io cannot open.
---

# Visio Draw.io SVG Diagrams

Use this skill for Visio-safe architecture diagrams. Prefer a `.drawio` source as the editable master, then generate SVG from that master.

## Core Workflow

1. Create or repair the `.drawio` file first.
2. Keep `.drawio` uncompressed and inline:
   - Use `<mxfile><diagram><mxGraphModel>...</mxGraphModel></diagram></mxfile>`.
   - Do not put raw XML as text inside `<diagram>`.
   - Do not use base64/deflate unless you are using draw.io's own exporter.
3. For stable line placement, use fixed point edges:
   - Edge cells should use `<mxGeometry relative="1" as="geometry">`.
   - Add `<mxPoint ... as="sourcePoint"/>` and `<mxPoint ... as="targetPoint"/>`.
   - Avoid relying on `source`/`target` auto-routing when the line layout must match a reference drawing.
4. Put elements in this order:
   - root cells `0` and `1`
   - title and layer/background rectangles
   - edges and edge labels
   - device/component boxes
5. Generate SVG from `.drawio` with `scripts/drawio_to_svg.py`.
6. Validate both files before handing them off.

## Use The Script

Run:

```bash
python <skill-dir>/scripts/drawio_to_svg.py input.drawio output.svg
```

The script reads inline draw.io XML and emits SVG with:

- fixed point edges copied from draw.io
- separate label text
- `clipPath` per box so text cannot spill outside frames
- conservative text wrapping for mixed Chinese/English labels
- UTF-8 output

If the input `.drawio` is compressed/base64 or lacks inline `mxGraphModel`, open it in draw.io and export as uncompressed XML, or repair it manually.

## Validation Checklist

Before final delivery:

- Parse `.drawio` and confirm `diagram` has an `mxGraphModel` child and empty text.
- Confirm every `mxGeometry` uses `as="geometry"`, not `as_="geometry"`.
- Confirm important Chinese labels still appear when reading files as UTF-8.
- Confirm SVG parses as XML.
- Render SVG through a browser or image pipeline and inspect:
  - no broken image icon
  - no text outside boxes
  - labels do not cover critical line endpoints
  - lines match the `.drawio` layout

Use `references/compatibility.md` for common failures and fixes.
