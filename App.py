#!/usr/bin/env python3
"""
Streamlit Mystery Mosaic Generator (fixed)
- Uses your 26-color fixed palette (1-9, A-S)
- Outputs 8.5" x 11" pages at 300 DPI (2550 x 3300 px)
- Robust text sizing (avoids AttributeError from textsize)
- Better error reporting for debugging in Streamlit
"""

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import os
import traceback

# ---------- CONFIG ----------
PAGE_WIDTH, PAGE_HEIGHT = 2550, 3300  # 8.5 x 11 inches at 300 DPI

PALETTE = {
    "1": (0, 0, 0), "2": (64, 64, 64), "3": (192, 192, 192),
    "4": (101, 67, 33), "5": (139, 69, 19), "6": (210, 180, 140),
    "7": (222, 184, 135), "8": (255, 253, 208), "9": (139, 0, 0),
    "A": (255, 0, 0), "B": (255, 69, 0), "C": (255, 140, 0),
    "D": (255, 255, 0), "E": (154, 205, 50), "F": (128, 128, 0),
    "G": (0, 128, 0), "H": (0, 255, 128), "I": (0, 100, 0),
    "J": (0, 0, 139), "K": (0, 0, 255), "L": (135, 206, 235),
    "M": (173, 216, 230), "N": (128, 0, 128), "O": (238, 130, 238),
    "P": (255, 0, 255), "Q": (230, 230, 250), "R": (231, 84, 128),
    "S": (255, 192, 203)
}

OUTLINE_WIDTH = 2
NUMBER_FILL = (0, 0, 0)
NUMBER_FONT_SIZE_FACTOR = 0.6  # relative to cell size

# ---------- UTILITIES ----------
def nearest_palette_label(rgb):
    """Return the palette key nearest to rgb (Euclidean in RGB)."""
    r, g, b = rgb
    best_label = None
    best_dist = None
    for k, v in PALETTE.items():
        dr = v[0] - r
        dg = v[1] - g
        db = v[2] - b
        dist = dr*dr + dg*dg + db*db
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_label = k
    return best_label

def resize_and_crop_to_page(im: Image.Image) -> Image.Image:
    """Resize image to cover the 8.5x11 page, then center-crop to exact size."""
    src_w, src_h = im.size
    scale = max(PAGE_WIDTH / src_w, PAGE_HEIGHT / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    im2 = im.resize((new_w, new_h), resample=Image.LANCZOS)
    left = (new_w - PAGE_WIDTH) // 2
    top = (new_h - PAGE_HEIGHT) // 2
    return im2.crop((left, top, left + PAGE_WIDTH, top + PAGE_HEIGHT))

def compute_cell_grid(grid_cols: int):
    """Compute integer cell size and rows to keep crisp square cells."""
    if grid_cols < 1:
        raise ValueError("grid_cols must be >= 1")
    cell_w = PAGE_WIDTH // grid_cols
    if cell_w < 1:
        raise ValueError("grid_cols too large for page width")
    grid_rows = PAGE_HEIGHT // cell_w
    if grid_rows < 1:
        raise ValueError("computed grid rows < 1; reduce grid_cols")
    return cell_w, grid_cols, grid_rows

def average_color_of_region(npimg: np.ndarray, left: int, top: int, w: int, h: int):
    """Return average RGB tuple for a rectangular region."""
    sub = npimg[top:top+h, left:left+w]
    if sub.size == 0:
        return (0, 0, 0)
    mean = sub.reshape(-1, 3).mean(axis=0)
    return (int(mean[0]), int(mean[1]), int(mean[2]))

def get_text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    """
    Robust text size measurement. Tries multiple methods to avoid AttributeError
    on environments where draw.textsize is missing.
    Returns (width, height)
    """
    # 1) try draw.textbbox (Pillow >= 8)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        pass

    # 2) try font.getbbox
    try:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        pass

    # 3) try font.getsize
    try:
        return font.getsize(text)
    except Exception:
        pass

    # 4) try draw.textsize
    try:
        return draw.textsize(text, font=font)
    except Exception:
        pass

    # 5) fallback estimate
    size = getattr(font, "size", 12)
    return int(len(text) * size * 0.6), int(size * 1.1)

def pil_image_to_bytes(img: Image.Image, fmt: str = "PNG"):
    """Return image bytes; set DPI for PNG/JPEG."""
    buf = io.BytesIO()
    fmt_up = fmt.upper()
    if fmt_up == "PNG":
        img.save(buf, format="PNG", dpi=(300, 300))
    elif fmt_up in ("JPG", "JPEG"):
        img.save(buf, format="JPEG", dpi=(300, 300), quality=95)
    else:
        img.save(buf, format=fmt)
    return buf.getvalue()

# ---------- CORE GENERATION ----------
def generate_mosaic_pages(pil_img: Image.Image, grid_cols: int = 60, use_truetype_font: bool = True):
    """
    Return (puzzle_img, solution_img) as PIL Images.
    """
    # prepare image
    im = resize_and_crop_to_page(pil_img.convert("RGB"))

    cell_w, cols, rows = compute_cell_grid(grid_cols)
    npimg = np.array(im)

    # compute label grid
    label_grid = []
    for r in range(rows):
        row_labels = []
        top = r * cell_w
        for c in range(cols):
            left = c * cell_w
            avg = average_color_of_region(npimg, left, top, cell_w, cell_w)
            label = nearest_palette_label(avg)
            row_labels.append(label)
        label_grid.append(row_labels)

    # build solution image
    solution = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), (255, 255, 255))
    draw_sol = ImageDraw.Draw(solution)
    for r in range(rows):
        top = r * cell_w
        for c in range(cols):
            left = c * cell_w
            label = label_grid[r][c]
            color = PALETTE[label]
            # integer coordinates keep rectangles crisp
            draw_sol.rectangle([left, top, left + cell_w - 1, top + cell_w - 1], fill=color)

    # build puzzle image (numbers + outlines)
    puzzle = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), (255, 255, 255))
    draw_puz = ImageDraw.Draw(puzzle)

    # determine font
    font_size = max(10, int(cell_w * NUMBER_FONT_SIZE_FACTOR))
    font = None
    if use_truetype_font:
        possible_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # linux
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/Library/Fonts/Arial.ttf",  # mac
            "C:\\Windows\\Fonts\\arial.ttf",  # windows
        ]
        for p in possible_fonts:
            try:
                if os.path.exists(p):
                    font = ImageFont.truetype(p, font_size)
                    break
            except Exception:
                font = None
        if font is None:
            # try a generic name (may work if font on PATH)
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
            except Exception:
                font = None

    if font is None:
        font = ImageFont.load_default()

    for r in range(rows):
        top = r * cell_w
        for c in range(cols):
            left = c * cell_w
            # draw white filled cell (clean)
            draw_puz.rectangle([left, top, left + cell_w - 1, top + cell_w - 1], fill=(255, 255, 255))
            # outline
            draw_puz.rectangle([left, top, left + cell_w - 1, top + cell_w - 1], outline=(0, 0, 0), width=OUTLINE_WIDTH)

            text = label_grid[r][c]
            tw, th = get_text_size(draw_puz, text, font)
            tx = left + (cell_w - tw) / 2
            ty = top + (cell_w - th) / 2
            # draw text (integers or letters)
            draw_puz.text((int(tx), int(ty)), text, fill=NUMBER_FILL, font=font)

    return puzzle, solution

# ---------- STREAMLIT UI ----------
st.set_page_config(layout="wide", page_title="Mystery Mosaic Generator")
st.title("🖌 Mystery Mosaic — Color-by-Number Generator (Streamlit)")

st.markdown(
    """
Upload an image and choose grid detail. The app produces:
- **Puzzle page** (numbers + outlines)
- **Solution page** (full color)

Both outputs are 8.5 x 11 inches at **300 DPI** (print-ready).
"""
)

uploaded_file = st.file_uploader("Upload an image (jpg, png)", type=["jpg", "jpeg", "png"])
grid_cols = st.slider("Number of columns (detail / difficulty)", min_value=20, max_value=200, value=60, step=1)

if uploaded_file:
    try:
        input_image = Image.open(uploaded_file)
    except Exception as e:
        st.error("Can't open uploaded image.")
        st.exception(e)
        input_image = None

    if input_image is not None:
        st.subheader("Original")
        st.image(input_image, use_column_width=True)

        if st.button("Generate Mosaic"):
            try:
                with st.spinner("Generating mosaic — this may take a few seconds..."):
                    puzzle_img, solution_img = generate_mosaic_pages(input_image, grid_cols)

                st.subheader("Puzzle Page (Numbers Only)")
                st.image(puzzle_img, use_column_width=True)

                st.subheader("Solution Page (Colored)")
                st.image(solution_img, use_column_width=True)

                # Download PNGs (with DPI)
                puzzle_bytes = pil_image_to_bytes(puzzle_img, "PNG")
                solution_bytes = pil_image_to_bytes(solution_img, "PNG")

                col1, col2, col3 = st.columns(3)
                col1.download_button("Download Puzzle PNG", data=puzzle_bytes, file_name="mosaic_puzzle.png", mime="image/png")
                col2.download_button("Download Solution PNG", data=solution_bytes, file_name="mosaic_solution.png", mime="image/png")

                # Combined PDF (solution first, puzzle second)
                try:
                    pdf_buf = io.BytesIO()
                    # convert to RGB to be safe
                    solution_img.convert("RGB").save(
                        pdf_buf, "PDF", resolution=300.0, save_all=True, append_images=[puzzle_img.convert("RGB")]
                    )
                    pdf_bytes = pdf_buf.getvalue()
                    col3.download_button("Download Both Pages PDF", data=pdf_bytes, file_name="mosaic_pages.pdf", mime="application/pdf")
                except Exception as e:
                    st.warning("Multi-page PDF export failed; offering PNGs instead. See console for details.")
                    st.text(traceback.format_exc())

            except Exception as e:
                st.error("An error occurred while generating the mosaic. Full traceback:")
                st.text(traceback.format_exc())
