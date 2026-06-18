# Visio Safe Diagrams

Generate draw.io and SVG architecture diagrams that are more likely to open cleanly in draw.io and import into Microsoft Visio.

This repository packages a small workflow, a Codex skill, and a converter script based on real compatibility issues:

- draw.io `atob` errors caused by malformed `.drawio` XML
- SVG files that render in a browser but fail in Visio
- text overflowing diagram boxes after export
- draw.io auto-routing moving connector lines away from the intended architecture layout

## Install In Codex

This repository also acts as a Codex plugin marketplace source.

```bash
codex plugin marketplace add balmytaotao-star/visio-safe-diagrams
```

Then open the Codex plugin directory, choose the "Visio Safe Diagrams" marketplace source, and install "Visio Safe Diagrams".

If your Codex surface does not support plugin installation yet, copy the skill folder directly:

```text
skills/visio-drawio-svg-diagrams/
```

into one of Codex's skill locations, such as:

```text
~/.agents/skills/
```

## Recommended Workflow

Use `.drawio` as the editable source of truth, then generate SVG from that file.

```bash
python scripts/drawio_to_svg.py examples/beckhoff_c6920_twincat_architecture.drawio output.svg
```

The converter expects an uncompressed, inline draw.io file:

```xml
<mxfile>
  <diagram>
    <mxGraphModel>
      <root>...</root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Do not store escaped raw XML as text inside `<diagram>`. That often makes draw.io treat the content as base64 and fail with:

```text
Failed to execute 'atob' on 'Window'
```

## What The Script Does

`scripts/drawio_to_svg.py` converts inline `.drawio` XML into a Visio-friendly SVG using simple primitives:

- `rect`
- `line`
- `text`
- `tspan`
- `clipPath`
- `marker`

It avoids `foreignObject`, external fonts, external images, scripts, filters, and CSS imports.

It also:

- preserves fixed point connector lines from draw.io
- places line labels as SVG text
- wraps mixed Chinese/English labels conservatively
- clips text inside each box so it cannot spill out
- writes UTF-8 SVG

## Codex Skill

The reusable Codex skill lives at:

```text
skills/visio-drawio-svg-diagrams/
```

Use it with a prompt like:

```text
Use $visio-drawio-svg-diagrams to repair this draw.io/SVG diagram so it opens in draw.io and imports into Visio without errors.
```

The skill includes:

- a concise workflow in `SKILL.md`
- compatibility notes in `references/compatibility.md`
- the converter script in `scripts/drawio_to_svg.py`

## Examples

The `examples/` folder contains a Beckhoff C6920 + TwinCAT 3.1 architecture diagram:

- `beckhoff_c6920_twincat_architecture.drawio`
- `beckhoff_c6920_twincat_architecture.svg`
- `beckhoff_c6920_twincat_architecture.png`

## Validation

Basic XML validation:

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('examples/beckhoff_c6920_twincat_architecture.drawio'); ET.parse('examples/beckhoff_c6920_twincat_architecture.svg'); print('ok')"
```

Confirm the draw.io file uses inline XML:

```bash
python -c "import xml.etree.ElementTree as ET; r=ET.parse('examples/beckhoff_c6920_twincat_architecture.drawio').getroot(); d=r.find('diagram'); print(d[0].tag, repr((d.text or '').strip()))"
```

Expected output:

```text
mxGraphModel ''
```

## License

MIT
