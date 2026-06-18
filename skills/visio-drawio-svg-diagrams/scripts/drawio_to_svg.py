from __future__ import annotations

import argparse
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"br", "div", "p"} and self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in {"div", "p"} and self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts).replace("\r", "\n")
        raw = re.sub(r"\n{2,}", "\n", raw)
        return "\n".join(line.strip() for line in raw.split("\n") if line.strip())


def html_to_lines(value: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html.unescape(value or ""))
    text = parser.text()
    return text.split("\n") if text else []


def parse_style(style: str) -> dict[str, str]:
    result = {}
    for item in (style or "").split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            result[key] = value
    return result


def geom(cell: ET.Element) -> dict[str, float]:
    g = cell.find("mxGeometry")
    if g is None:
        return {}
    out = {}
    for key in ("x", "y", "width", "height"):
        if key in g.attrib:
            out[key] = float(g.attrib[key])
    return out


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def text_width_units(text: str) -> float:
    units = 0.0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff" or ch in "，。；：、（）×":
            units += 1.0
        elif ch.isspace():
            units += 0.35
        elif ch in "ilI1.,:/|":
            units += 0.35
        elif ch.isupper():
            units += 0.72
        else:
            units += 0.58
    return units


def wrap_line(line: str, max_units: float) -> list[str]:
    if text_width_units(line) <= max_units:
        return [line]
    chunks: list[str] = []
    current = ""
    for token in re.findall(r"[A-Za-z0-9_.:/+-]+|\s+|.", line):
        candidate = current + token
        if current and text_width_units(candidate) > max_units:
            chunks.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks


def wrap_lines(lines: list[str], max_width: float, font_size: float) -> list[str]:
    max_units = max_width / (font_size * 0.72)
    out: list[str] = []
    for line in lines:
        out.extend(wrap_line(line, max_units))
    return out


def svg_text(lines: list[str], x: float, y: float, font_size: float, color: str, weight: str = "400", anchor: str = "start", line_height: float | None = None) -> str:
    if not lines:
        return ""
    lh = line_height or font_size * 1.35
    spans = [
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Microsoft YaHei, Segoe UI, Arial, sans-serif" '
        f'font-size="{font_size:.1f}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">'
    ]
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else lh
        spans.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    spans.append("</text>")
    return "".join(spans)


def draw_vertex(cell: ET.Element, clip_id: str) -> str:
    style = parse_style(cell.attrib.get("style", ""))
    g = geom(cell)
    x, y = g.get("x", 0), g.get("y", 0)
    w, h = g.get("width", 0), g.get("height", 0)
    lines = html_to_lines(cell.attrib.get("value", ""))
    parts: list[str] = []
    is_text = style.get("strokeColor") == "none" and style.get("fillColor") == "none"

    if is_text:
        color = style.get("fontColor", "#162033")
        size = float(style.get("fontSize", "14"))
        anchor = "middle" if style.get("align") == "center" else "start"
        tx = x + w / 2 if anchor == "middle" else x
        if cell.attrib.get("id") == "title":
            parts.append(svg_text(lines[:1], tx, y + 32, 28, "#162033", "700", anchor))
            if len(lines) > 1:
                parts.append(svg_text(lines[1:], tx, y + 58, 15, "#566275", "400", anchor))
        else:
            wrapped = wrap_lines(lines, max(w - 4, 40), size)
            parts.append(svg_text(wrapped, tx, y + h / 2 + size * 0.35, size, color, "700", anchor))
        return "\n".join(parts)

    fill = style.get("fillColor", "#ffffff")
    stroke = style.get("strokeColor", "#334155")
    radius = 8 if style.get("rounded") == "1" else 0
    parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    parts.append(f'<clipPath id="{clip_id}"><rect x="{x + 8:.1f}" y="{y + 6:.1f}" width="{max(w - 16, 0):.1f}" height="{max(h - 12, 0):.1f}" rx="{radius}"/></clipPath>')
    parts.append(f'<g clip-path="url(#{clip_id})">')
    if lines:
        title = lines[0]
        body = lines[1:]
        title_size = 18 if w >= 180 else 16
        body_size = 13 if h >= 90 else 12
        title_y = y + 29
        body_y = y + 53
        title_lh = title_size * 1.2
        body_lh = body_size * 1.28
        if cell.attrib.get("id", "").startswith("layer"):
            title_size = 20
            body_size = 14
            title_y = y + 31
            body_y = y + 62
            title_lh = title_size * 1.25
            body_lh = body_size * 1.35
        title_lines = wrap_lines([title], max(w - 36, 40), title_size)
        body_lines = wrap_lines(body, max(w - 36, 40), body_size)
        available = (y + h - 10) - body_y
        max_body = max(0, int(available // body_lh) + 1)
        body_lines = body_lines[:max_body]
        parts.append(svg_text(title_lines, x + 18, title_y, title_size, "#162033", "700", "start", title_lh))
        if body_lines:
            parts.append(svg_text(body_lines, x + 18, body_y, body_size, "#334155", "400", "start", body_lh))
    parts.append("</g>")
    return "\n".join(parts)


def draw_edge(cell: ET.Element, marker_ids: dict[str, str]) -> str:
    style = parse_style(cell.attrib.get("style", ""))
    g = cell.find("mxGeometry")
    if g is None:
        return ""
    points = list(g.findall("mxPoint"))
    if len(points) < 2:
        return ""
    x1, y1 = points[0].attrib["x"], points[0].attrib["y"]
    x2, y2 = points[1].attrib["x"], points[1].attrib["y"]
    color = style.get("strokeColor", "#2d3a4a")
    width = style.get("strokeWidth", "3")
    dash = ' stroke-dasharray="8 8"' if style.get("dashed") == "1" else ""
    marker = f' marker-end="url(#{marker_ids[color]})"' if style.get("endArrow") == "block" else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash}{marker} fill="none"/>'


def convert(input_path: Path, output_path: Path):
    tree = ET.parse(input_path)
    graph = tree.getroot().find("./diagram/mxGraphModel")
    if graph is None:
        raise SystemExit("draw.io file must contain inline ./diagram/mxGraphModel, not encoded diagram text")
    width = float(graph.attrib.get("pageWidth", "1600"))
    height = float(graph.attrib.get("pageHeight", "1100"))
    root = graph.find("root")
    if root is None:
        raise SystemExit("mxGraphModel has no root")

    cells = [cell for cell in root if cell.attrib.get("id") not in {"0", "1"}]
    edge_colors: list[str] = []
    for cell in cells:
        if cell.attrib.get("edge") == "1":
            color = parse_style(cell.attrib.get("style", "")).get("strokeColor", "#2d3a4a")
            if color not in edge_colors:
                edge_colors.append(color)
    marker_ids = {color: f"arrow_{idx}" for idx, color in enumerate(edge_colors)}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
        "<defs>",
    ]
    for color, marker_id in marker_ids.items():
        parts.append(
            f'<marker id="{marker_id}" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth">'
            f'<path d="M2,2 L10,6 L2,10 z" fill="{color}"/></marker>'
        )
    parts.append("</defs>")
    parts.append(f'<rect width="{int(width)}" height="{int(height)}" fill="#f7f9fb"/>')

    clip_idx = 0
    for cell in cells:
        if cell.attrib.get("edge") == "1":
            parts.append(draw_edge(cell, marker_ids))
        elif cell.attrib.get("vertex") == "1":
            clip_idx += 1
            parts.append(draw_vertex(cell, f"clip_{clip_idx}"))

    parts.append("</svg>")
    output_path.write_text("\n".join(parts), encoding="utf-8")
    ET.parse(output_path)


def main():
    parser = argparse.ArgumentParser(description="Convert an inline uncompressed draw.io file to Visio-friendly SVG.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    convert(args.input, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
