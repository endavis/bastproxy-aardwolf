"""A bar chart as a standalone SVG document.

The web plugin serves the string as it is, so every label is escaped here. The chart holds no
script, no event attribute and no link.
"""

from collections.abc import Sequence
from html import escape

BAR_WIDTH = 28
BAR_GAP = 12
MARGIN_LEFT = 60
MARGIN_RIGHT = 20
MARGIN_TOP = 40
PLOT_HEIGHT = 220
MARGIN_BOTTOM = 80
MIN_WIDTH = 360
MAX_LABEL = 14


def _number(value: float) -> str:
    """Format a value: whole numbers without decimals, others with two."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def _short(label: str) -> str:
    """Shorten a label so it fits under its bar."""
    return label if len(label) <= MAX_LABEL else label[: MAX_LABEL - 2] + ".."


def bar_chart_svg(title: str, bars: Sequence[tuple[str, float]], unit: str) -> str:
    """Draw ``bars``, a list of ``(label, value)``, as an SVG document.

    Args:
        title: The heading drawn above the bars.
        bars: The label and value of each bar, left to right.
        unit: The unit of the values, shown in the axis note.

    Returns:
        The SVG text. With no bars it says "No data".
    """
    width = max(MIN_WIDTH, MARGIN_LEFT + MARGIN_RIGHT + len(bars) * (BAR_WIDTH + BAR_GAP))
    height = MARGIN_TOP + PLOT_HEIGHT + MARGIN_BOTTOM
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{MARGIN_LEFT}" y="24" font-size="16" fill="#222222">'
        f"{escape(title, quote=True)}</text>",
    ]
    if not bars:
        parts.append(
            f'<text x="{MARGIN_LEFT}" y="{MARGIN_TOP + 40}" font-size="14" fill="#666666">'
            "No data</text>"
        )
        parts.append("</svg>")
        return "".join(parts)

    peak = max(max(value for _, value in bars), 0.0)
    scale = PLOT_HEIGHT / peak if peak > 0 else 0.0
    base = MARGIN_TOP + PLOT_HEIGHT
    parts.append(
        f'<line x1="{MARGIN_LEFT}" y1="{base}" x2="{width - MARGIN_RIGHT}" y2="{base}" '
        'stroke="#444444"/>'
    )
    parts.append(
        f'<text x="{MARGIN_LEFT - 8}" y="{MARGIN_TOP + 4}" font-size="11" text-anchor="end" '
        f'fill="#444444">{escape(_number(peak), quote=True)}</text>'
    )
    parts.append(
        f'<text x="{MARGIN_LEFT - 8}" y="{base}" font-size="11" text-anchor="end" '
        'fill="#444444">0</text>'
    )
    if unit:
        parts.append(
            f'<text x="{width - MARGIN_RIGHT}" y="24" font-size="11" text-anchor="end" '
            f'fill="#666666">{escape(unit, quote=True)}</text>'
        )
    for index, (label, value) in enumerate(bars):
        left = MARGIN_LEFT + BAR_GAP + index * (BAR_WIDTH + BAR_GAP)
        bar_height = max(value, 0.0) * scale
        top = base - bar_height
        tip = escape(f"{label}: {_number(value)} {unit}".strip(), quote=True)
        parts.append(
            f'<rect x="{left}" y="{top:.1f}" width="{BAR_WIDTH}" height="{bar_height:.1f}" '
            f'fill="#3b78c4"><title>{tip}</title></rect>'
        )
        centre = left + BAR_WIDTH // 2
        parts.append(
            f'<text x="{centre}" y="{base + 14}" font-size="10" text-anchor="end" '
            f'fill="#333333" transform="rotate(-45 {centre} {base + 14})">'
            f"{escape(_short(label), quote=True)}</text>"
        )
    parts.append("</svg>")
    return "".join(parts)
