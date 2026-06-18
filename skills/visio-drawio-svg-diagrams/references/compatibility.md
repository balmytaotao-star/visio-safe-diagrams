# Draw.io / SVG / Visio Compatibility Notes

## Draw.io `atob` Error

Symptom:

`Failed to execute 'atob' on 'Window': The string to be decoded contains characters outside of the Latin1 range.`

Cause:

The `.drawio` file usually has raw `mxGraphModel` XML escaped as text inside `<diagram>`. draw.io interprets diagram text as compressed/base64 payload and tries to decode it.

Fix:

Use inline XML:

```xml
<mxfile>
  <diagram id="..." name="...">
    <mxGraphModel>
      <root>...</root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Do not use:

```xml
<diagram>&lt;mxGraphModel&gt;...&lt;/mxGraphModel&gt;</diagram>
```

## Python ElementTree Geometry Attribute

When creating draw.io XML with Python, `as` is a reserved Python keyword. Do not write:

```python
ET.SubElement(cell, "mxGeometry", as_="geometry")
```

That emits `as_="geometry"`, which draw.io does not understand.

Write:

```python
ET.SubElement(cell, "mxGeometry", {"as": "geometry"})
```

## Stable Lines

For architecture diagrams that must visually match a reference, avoid draw.io auto-routing:

```xml
<mxCell edge="1" parent="1" style="endArrow=block;html=1;rounded=0;strokeColor=#20825d;strokeWidth=3;">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="325" y="315" as="sourcePoint"/>
    <mxPoint x="325" y="470" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

Use labels as separate text vertices rather than edge values when exact placement matters.

## SVG Text Overflow

SVG does not implement draw.io's `whiteSpace=wrap` behavior automatically. When exporting manually:

- Convert HTML values into plain lines.
- Wrap by approximate text width.
- Use `clipPath` inside each box.
- Keep font sizes modest for small boxes.
- Prefer `Microsoft YaHei, Segoe UI, Arial, sans-serif` for mixed Chinese/English diagrams on Windows.

## Visio Import

Visio is stricter than browsers about malformed SVG. Keep SVG simple:

- Avoid embedded HTML/foreignObject.
- Avoid external fonts, external images, CSS imports, scripts, filters, and masks.
- Use basic shapes: `rect`, `line`, `text`, `tspan`, `clipPath`, `marker`.
- Write UTF-8 XML.
- Prefer explicit coordinates over layout-dependent CSS.

## Quick Checks

Useful checks:

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('diagram.drawio'); ET.parse('diagram.svg'); print('ok')"
python -c "import xml.etree.ElementTree as ET; r=ET.parse('diagram.drawio').getroot(); d=r.find('diagram'); print(d[0].tag, repr((d.text or '').strip()))"
```
