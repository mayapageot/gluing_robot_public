#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_pres2.py — Glue analysis report generator (PPTX) — FINAL

Slides:
1) Title
2) Simple TOC
3) All measurements (compact table, no photos)
4) Statistics
5) Histograms (radius + accum) -> always centered & same size
6) One slide per image: photo (left) + compact "Measurements" card (right)

Deps:
  pip install python-pptx pillow pandas numpy matplotlib
"""

import argparse
import io
import tempfile
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# =======================
# Calibration (edit)
# =======================
PIXEL_TO_UM = 1.24  # µm/pixel


# =======================
# Theme / Style
# =======================
PRIMARY = RGBColor(28, 54, 104)       # deep blue
SECONDARY = RGBColor(240, 244, 250)   # very light blue/grey
BORDER = RGBColor(210, 217, 230)
TEXT = RGBColor(25, 25, 25)
WHITE = RGBColor(255, 255, 255)

FONT_MAIN = "Calibri"
FONT_MONO = "Consolas"


# =======================
# Slide geometry (16:9)
# =======================
SLIDE_W = 16.0
SLIDE_H = 9.0

TOP_BAR_H = 0.60          # inches
MARGIN_X = 0.60
CONTENT_TOP = 0.85        # below bar
BOTTOM_MARGIN = 0.35

CONTENT_W = SLIDE_W - 2 * MARGIN_X
CONTENT_H = SLIDE_H - CONTENT_TOP - BOTTOM_MARGIN


# =======================
# Utilities
# =======================
def safe_str(x) -> str:
    return "" if pd.isna(x) else str(x)


def infer_pictures_root(csv_path: Path) -> Path:
    # If CSV is .../Pictures/analysis/YYYY-MM-DD.csv -> root is .../Pictures
    if csv_path.parent.name.lower() == "analysis":
        return csv_path.parent.parent
    return csv_path.parent


def build_image_index(pictures_root: Path, exts=(".bmp", ".png", ".jpg", ".jpeg")) -> dict:
    """filename -> full path (first occurrence). One recursive scan."""
    index = {}
    for ext in exts:
        for fp in pictures_root.rglob(f"*{ext}"):
            if fp.name not in index:
                index[fp.name] = fp
    return index


def resize_image_to_stream(image_path: Path, max_width_px: int = 1900) -> io.BytesIO:
    """Resize image for PPT and return PNG bytes (keeps aspect ratio)."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if w > max_width_px:
            scale = max_width_px / float(w)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio


# =======================
# PPT helpers
# =======================
def add_top_bar(slide, left_text: str = "", right_text: str = ""):
    """Top colored bar across the slide."""
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(SLIDE_W), Inches(TOP_BAR_H))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY
    bar.line.color.rgb = PRIMARY

    if left_text:
        tb = slide.shapes.add_textbox(Inches(0.55), Inches(0.12), Inches(11.0), Inches(0.35))
        tf = tb.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = left_text
        p.font.name = FONT_MAIN
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = WHITE

    if right_text:
        tb = slide.shapes.add_textbox(Inches(11.8), Inches(0.12), Inches(3.6), Inches(0.35))
        tf = tb.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        p.text = right_text
        p.font.name = FONT_MAIN
        p.font.size = Pt(13)
        p.font.bold = False
        p.font.color.rgb = WHITE


def add_card(slide, x, y, w, h, fill=SECONDARY, line=BORDER):
    """Light card background (rectangle)."""
    shp = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(1.0)
    return shp


def set_cell_style(cell, font_size=11, bold=False, color=TEXT,
                   align="left", fill=None, font_name=FONT_MAIN):
    """
    Style a python-pptx table cell.
    NOTE: table cells do NOT support borders (no cell.line).
    """
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill

    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]

    if align == "center":
        p.alignment = PP_ALIGN.CENTER
    elif align == "right":
        p.alignment = PP_ALIGN.RIGHT
    else:
        p.alignment = PP_ALIGN.LEFT

    p.font.name = font_name
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color


def add_title_slide(prs: Presentation, title: str, subtitle_lines: list[str]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    add_top_bar(slide, "Glue analysis report", datetime.now().strftime("%Y-%m-%d"))

    # Title
    tb = slide.shapes.add_textbox(Inches(0.9), Inches(2.0), Inches(14.2), Inches(1.2))
    tf = tb.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_MAIN
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = PRIMARY

    # Subtitle card
    add_card(slide, 1.0, 3.35, 14.0, 3.2, fill=SECONDARY, line=SECONDARY)
    tb2 = slide.shapes.add_textbox(Inches(1.35), Inches(3.65), Inches(13.3), Inches(2.8))
    tf2 = tb2.text_frame
    tf2.clear()
    for i, line in enumerate(subtitle_lines):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = line
        p.font.name = FONT_MAIN
        p.font.size = Pt(20)
        p.font.color.rgb = TEXT


def add_toc_slide(prs: Presentation, items: list[str]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_top_bar(slide, "Contents")

    add_card(slide, 1.0, 1.25, 14.0, 7.15, fill=SECONDARY, line=SECONDARY)
    tb = slide.shapes.add_textbox(Inches(1.4), Inches(1.6), Inches(13.2), Inches(6.6))
    tf = tb.text_frame
    tf.clear()

    p0 = tf.paragraphs[0]
    p0.text = "Contents"
    p0.font.name = FONT_MAIN
    p0.font.size = Pt(34)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY

    for it in items:
        p = tf.add_paragraph()
        p.text = f"• {it}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(24)
        p.font.color.rgb = TEXT


# =======================
# All measurements table slide
# =======================
def add_all_measurements_table_slide(prs: Presentation, df: pd.DataFrame, max_rows: int = 30):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_top_bar(slide, "All measurements (table)")

    df2 = df.copy()
    if "radius" in df2.columns and "radius_um" not in df2.columns:
        df2["radius_um"] = df2["radius"] * PIXEL_TO_UM

    preferred_cols = [
        "image_file", "Chip_name", "support_name", "dot_pos",
        "radius_um", "accum", "Area"
    ]
    cols = [c for c in preferred_cols if c in df2.columns]
    if not cols:
        tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(14.0), Inches(1.0))
        tb.text_frame.text = "No expected columns found in the CSV."
        return

    df_show = df2[cols].head(max_rows).reset_index(drop=True)

    x, y, w, h = MARGIN_X, CONTENT_TOP, CONTENT_W, CONTENT_H
    rows = len(df_show) + 1
    cols_n = len(cols)

    table = slide.shapes.add_table(rows, cols_n, Inches(x), Inches(y), Inches(w), Inches(h)).table

    # Column widths (balanced)
    width_map = {c: 2.0 for c in cols}
    if "image_file" in cols:   width_map["image_file"] = 3.6
    if "Chip_name" in cols:    width_map["Chip_name"] = 2.2
    if "support_name" in cols: width_map["support_name"] = 2.4
    if "dot_pos" in cols:      width_map["dot_pos"] = 1.4
    if "radius_um" in cols:    width_map["radius_um"] = 1.6
    if "accum" in cols:        width_map["accum"] = 1.4
    if "Area" in cols:         width_map["Area"] = 1.4

    total = sum(width_map[c] for c in cols)
    scale = w / total
    for j, c in enumerate(cols):
        table.columns[j].width = Inches(width_map[c] * scale)

    # Header
    for j, c in enumerate(cols):
        hdr = "radius (µm)" if c == "radius_um" else c
        cell = table.cell(0, j)
        cell.text = hdr
        set_cell_style(cell, font_size=11, bold=True, color=WHITE, align="center", fill=PRIMARY)

    # Body rows (zebra)
    for i in range(len(df_show)):
        zebra = RGBColor(255, 255, 255) if i % 2 == 0 else RGBColor(248, 250, 254)
        for j, c in enumerate(cols):
            v = df_show.loc[i, c]
            if pd.isna(v):
                s = ""
            elif c == "accum":
                s = f"{float(v):.3f}"
            elif c == "radius_um":
                s = f"{float(v):.1f}"
            elif c == "Area":
                s = f"{float(v):.0f}"
            else:
                s = str(v)

            cell = table.cell(i + 1, j)
            cell.text = s
            set_cell_style(cell, font_size=9, bold=False, color=TEXT, align="left", fill=zebra)

    # Footnote
    if len(df2) > max_rows:
        note = slide.shapes.add_textbox(Inches(0.8), Inches(8.55), Inches(14.4), Inches(0.3))
        tf = note.text_frame
        tf.text = f"Showing first {max_rows} rows out of {len(df2)}."
        tf.paragraphs[0].font.size = Pt(11)
        tf.paragraphs[0].font.color.rgb = TEXT


# =======================
# Stats slide
# =======================
def add_stats_slide(prs: Presentation, df: pd.DataFrame):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_top_bar(slide, "Statistics")

    df2 = df.copy()
    if "radius" in df2.columns:
        df2["radius_um"] = df2["radius"] * PIXEL_TO_UM

    lines = []
    if "radius_um" in df2.columns and df2["radius_um"].notna().any():
        r = df2["radius_um"].dropna()
        lines.append(f"Radius (µm): mean={r.mean():.1f}   std={r.std(ddof=1):.1f}   min={r.min():.1f}   max={r.max():.1f}")
        lines.append(f"Radius (µm): median={r.median():.1f}   IQR={(r.quantile(0.75)-r.quantile(0.25)):.1f}")
    else:
        lines.append("Radius: not available in CSV.")

    if "accum" in df2.columns and df2["accum"].notna().any():
        a = df2["accum"].dropna()
        lines.append(f"Accum: mean={a.mean():.3f}   std={a.std(ddof=1):.3f}   min={a.min():.3f}   max={a.max():.3f}")
    else:
        lines.append("Accum: not available in CSV.")

    n_rows = len(df2)
    n_imgs = df2["image_file"].nunique() if "image_file" in df2.columns else None
    lines.append(f"Counts: rows={n_rows}" + (f", unique images={n_imgs}" if n_imgs is not None else ""))

    add_card(slide, 1.0, 1.35, 14.0, 6.9, fill=SECONDARY, line=SECONDARY)
    tb = slide.shapes.add_textbox(Inches(1.45), Inches(1.75), Inches(13.1), Inches(6.2))
    tf = tb.text_frame
    tf.clear()

    for i, s in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = s
        p.font.name = FONT_MAIN
        p.font.size = Pt(24)
        p.font.color.rgb = TEXT


# =======================
# Histogram (centered and same size)
# =======================
def _save_hist_png(values: np.ndarray, xlabel: str, title: str, bins: int = 20) -> str:
    """
    Create a PNG already sized for the slide content area so placement is perfect.
    """
    fig_w = CONTENT_W
    fig_h = CONTENT_H
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    ax = fig.add_subplot(111)

    ax.hist(values, bins=bins)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.grid(True, alpha=0.2)

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.95])

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150)
    plt.close(fig)
    return tmp.name


def add_hist_slide(prs: Presentation, title: str, values: np.ndarray, xlabel: str, bins: int = 20):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_top_bar(slide, title)

    png_path = _save_hist_png(values, xlabel=xlabel, title=title, bins=bins)

    # Exactly fill the content area (always centered)
    slide.shapes.add_picture(
        png_path,
        Inches(MARGIN_X),
        Inches(CONTENT_TOP),
        width=Inches(CONTENT_W),
        height=Inches(CONTENT_H),
    )


# =======================
# Per-image slide (photo + compact card)
# =======================
def add_image_slide(prs: Presentation, img_path: Path, slide_title: str, df_img: pd.DataFrame):
    """
    Layout:
      - left: photo (fills left area, clean)
      - right: compact Measurements card (nice sized table)
      - footer: filename
    """
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_top_bar(slide, slide_title)

    gap = 0.35
    left_w = 10.2
    right_w = CONTENT_W - left_w - gap

    left_x = MARGIN_X
    right_x = MARGIN_X + left_w + gap
    y0 = CONTENT_TOP

    # Photo: fixed width+height to fill the area neatly
    img_stream = resize_image_to_stream(img_path, max_width_px=2200)
    slide.shapes.add_picture(img_stream, Inches(left_x), Inches(y0), width=Inches(left_w), height=Inches(CONTENT_H))

    # Right card
    card_h = 4.10
    add_card(slide, right_x, y0, right_w, card_h, fill=SECONDARY, line=BORDER)

    # Card title
    tb = slide.shapes.add_textbox(Inches(right_x + 0.25), Inches(y0 + 0.18), Inches(right_w - 0.50), Inches(0.35))
    tf = tb.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = "Measurements"
    p.font.name = FONT_MAIN
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY

    # Prepare df
    tdf = df_img.copy()
    if "radius" in tdf.columns:
        tdf["radius_um"] = tdf["radius"] * PIXEL_TO_UM

    cols = []
    if "dot_pos" in tdf.columns:
        cols.append("dot_pos")
    if "radius_um" in tdf.columns:
        cols.append("radius_um")
    if "accum" in tdf.columns:
        cols.append("accum")

    if not cols:
        tb2 = slide.shapes.add_textbox(Inches(right_x + 0.25), Inches(y0 + 0.70), Inches(right_w - 0.50), Inches(1.0))
        tb2.text_frame.text = "No measurements available for this image."
    else:
        if "dot_pos" in tdf.columns:
            tdf = tdf.sort_values("dot_pos")

        tdf_show = tdf[cols].head(6).reset_index(drop=True)
        rows = len(tdf_show) + 1
        cols_n = len(cols)

        table_x = right_x + 0.25
        table_y = y0 + 0.68
        table_w = right_w - 0.50
        table_h = 3.20

        table = slide.shapes.add_table(
            rows, cols_n, Inches(table_x), Inches(table_y), Inches(table_w), Inches(table_h)
        ).table

        # Column widths inside card (nice proportions)
        base = []
        for c in cols:
            if c == "dot_pos":
                base.append(1.25)
            elif c == "radius_um":
                base.append(1.75)
            else:
                base.append(1.25)

        total = sum(base)
        scale = table_w / total
        for j, bw in enumerate(base):
            table.columns[j].width = Inches(bw * scale)

        # Header
        for j, c in enumerate(cols):
            hdr = "dot_pos" if c == "dot_pos" else ("Radius (µm)" if c == "radius_um" else "accum")
            cell = table.cell(0, j)
            cell.text = hdr
            set_cell_style(cell, font_size=12, bold=True, color=WHITE, align="center", fill=PRIMARY)

        # Body zebra
        for i in range(len(tdf_show)):
            zebra = WHITE if i % 2 == 0 else RGBColor(248, 250, 254)
            for j, c in enumerate(cols):
                v = tdf_show.loc[i, c]
                if pd.isna(v):
                    s = ""
                elif c == "radius_um":
                    s = f"{float(v):.1f}"
                elif c == "accum":
                    s = f"{float(v):.3f}"
                else:
                    s = str(v)

                cell = table.cell(i + 1, j)
                cell.text = s
                align = "left" if c == "dot_pos" else "center"
                set_cell_style(cell, font_size=12, bold=False, color=TEXT, align=align, fill=zebra)

    # Footer
    footer_y = y0 + card_h + 0.25
    footer_h = 0.85
    add_card(slide, right_x, footer_y, right_w, footer_h, fill=SECONDARY, line=BORDER)

    tb3 = slide.shapes.add_textbox(Inches(right_x + 0.25), Inches(footer_y + 0.22), Inches(right_w - 0.50), Inches(0.45))
    tf3 = tb3.text_frame
    tf3.clear()
    p = tf3.paragraphs[0]
    p.text = f"File: {img_path.name}"
    p.font.name = FONT_MONO
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT


# =======================
# Main
# =======================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to analysis CSV (e.g. .../Pictures/analysis/YYYY-MM-DD.csv)")
    ap.add_argument("--pictures-root", default=None, help="Root folder containing images (defaults inferred from CSV)")
    ap.add_argument("--out", default=None, help="Output pptx path (default: same name as CSV, .pptx)")
    ap.add_argument("--title", default="Glue analysis report", help="Presentation title")
    ap.add_argument("--max-table-rows", type=int, default=30, help="Max rows shown in the table slide")
    args = ap.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    pictures_root = Path(args.pictures_root).expanduser().resolve() if args.pictures_root else infer_pictures_root(csv_path)
    if not pictures_root.exists():
        raise FileNotFoundError(f"Pictures root not found: {pictures_root}")

    out_path = Path(args.out).expanduser().resolve() if args.out else csv_path.with_suffix(".pptx")

    df = pd.read_csv(csv_path)
    if "image_file" not in df.columns:
        raise ValueError("CSV must contain an 'image_file' column.")

    img_index = build_image_index(pictures_root)
    unique_images = list(pd.Series(df["image_file"].dropna().unique()))
    missing = [f for f in unique_images if f not in img_index]
    if missing:
        print(f"[WARN] {len(missing)} images not found under {pictures_root}. Example(s):")
        for m in missing[:8]:
            print("  -", m)

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    subtitle = [
        f"CSV: {csv_path.name}",
        f"Pictures root: {pictures_root}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Calibration: {PIXEL_TO_UM:.3f} µm/px",
    ]
    add_title_slide(prs, args.title, subtitle)

    n_imgs = df["image_file"].nunique()
    toc_items = [
        "All measurements (table)",
        "Statistics",
        "Distributions (histograms)",
        f"Per-image slides ({n_imgs} images)",
    ]
    add_toc_slide(prs, toc_items)

    add_all_measurements_table_slide(prs, df, max_rows=args.max_table_rows)
    add_stats_slide(prs, df)

    # Histograms (perfectly centered)
    df2 = df.copy()
    if "radius" in df2.columns and df2["radius"].notna().any():
        df2["radius_um"] = df2["radius"] * PIXEL_TO_UM
        add_hist_slide(prs, "Radius distribution", df2["radius_um"].dropna().values, "Radius (µm)", bins=20)

    if "accum" in df2.columns and df2["accum"].notna().any():
        add_hist_slide(prs, "Fit quality (accum) distribution", df2["accum"].dropna().values, "accum", bins=20)

    # One slide per image
    for img_file in sorted(unique_images):
        if img_file not in img_index:
            continue
        img_path = img_index[img_file]
        df_img = df[df["image_file"] == img_file]

        chip = safe_str(df_img["Chip_name"].iloc[0]) if "Chip_name" in df_img.columns and len(df_img) else ""
        sup = safe_str(df_img["support_name"].iloc[0]) if "support_name" in df_img.columns and len(df_img) else ""

        title = f"{chip} on {sup} — {img_file}".strip(" —") if (chip or sup) else img_file
        add_image_slide(prs, img_path, title, df_img)

    prs.save(out_path)
    print(f"[OK] PowerPoint created: {out_path}")


if __name__ == "__main__":
    main()
