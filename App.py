

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import math

# ---------- CONFIG ----------
PAGE_WIDTH, PAGE_HEIGHT = 2550, 3300  # 8.5x11 at 300 DPI
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
PALETTE_KEYS = list(PALETTE.keys())

OUTLINE_WIDTH = 2
NUMBER_FILL = (0, 0, 0)
NUMBER_FONT_SIZE_FACTOR = 0.6

# ---------- FUNCTIONS ----------
def nearest_palette_label(rgb):
    r,g,b = rgb
    best_label = None
    best_dist = None
    for k, v in PALETTE.items():
        dr, dg, db = v[0]-r, v[1]-g, v[2]-b
        dist = dr*dr + dg*dg + db*db
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_label = k
    return best_label

def resize_and_crop(im):
    src_w, src_h = im.size
    scale = max(PAGE_WIDTH / src_w, PAGE_HEIGHT / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    im2 = im.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - PAGE_WIDTH) // 2
    top = (new_h - PAGE_HEIGHT) // 2
    return im2.crop((left, top, left + PAGE_WIDTH, top + PAGE_HEIGHT))

def compute_cell_grid(grid_cols):
    cell_w = PAGE_WIDTH // grid_cols
    grid_rows = PAGE_HEIGHT // cell_w
    return cell_w, grid_cols, grid_rows

def average_color_of_region(npimg, left, top, w, h):
    sub = npimg[top:top+h, left:left+w]
    mean = sub.reshape(-1, 3).mean(axis=0)
    return (int(mean[0]), int(mean[1]), int(mean[2]))

def generate_mosaic_pages(im, grid_cols):
    im = resize_and_crop(im.convert("RGB"))
    cell_w, cols, rows = compute_cell_grid(grid_cols)
    npimg = np.array(im)

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

    # Solution image
    solution = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), (255,255,255))
    draw_sol = ImageDraw.Draw(solution)
    for r in range(rows):
        top = r * cell_w
        for c in range(cols):
            left = c * cell_w
            draw_sol.rectangle(
                [left, top, left+cell_w-1, top+cell_w-1],
                fill=PALETTE[label_grid[r][c]]
            )

    # Puzzle image
    puzzle = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), (255,255,255))
    draw_puz = ImageDraw.Draw(puzzle)
    font_size = max(10, int(cell_w * NUMBER_FONT_SIZE_FACTOR))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    for r in range(rows):
        top = r * cell_w
        for c in range(cols):
            left = c * cell_w
            draw_puz.rectangle([left, top, left+cell_w-1, top+cell_w-1],
                               outline=(0,0,0), width=OUTLINE_WIDTH)
            text = label_grid[r][c]
            tw, th = draw_puz.textsize(text, font=font)
            tx = left + (cell_w - tw) / 2
            ty = top + (cell_w - th) / 2
            draw_puz.text((tx, ty), text, fill=NUMBER_FILL, font=font)

    return puzzle, solution

def img_to_bytes(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

# ---------- STREAMLIT UI ----------
st.title("🖌 Mystery Mosaic Color-by-Number Generator")
st.write("Upload an image, choose grid size, and download print-ready puzzle & solution pages.")

uploaded_file = st.file_uploader("Upload an image", type=["jpg","jpeg","png"])
grid_cols = st.slider("Number of columns (difficulty/detail)", min_value=20, max_value=150, value=60)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Original Image", use_container_width=True)

    if st.button("Generate Mosaic"):
        puzzle_img, solution_img = generate_mosaic_pages(image, grid_cols)

        st.subheader("Puzzle Page (Numbers Only)")
        st.image(puzzle_img, use_container_width=True)

        st.subheader("Solution Page (Colored)")
        st.image(solution_img, use_container_width=True)

        # Download buttons
        st.download_button(
            "Download Puzzle PNG",
            data=img_to_bytes(puzzle_img, "PNG"),
            file_name="puzzle.png",
            mime="image/png"
        )
        st.download_button(
            "Download Solution PNG",
            data=img_to_bytes(solution_img, "PNG"),
            file_name="solution.png",
            mime="image/png"
        )

        # PDF (two pages)
        pdf_buf = io.BytesIO()
        solution_img.save(pdf_buf, "PDF", resolution=300.0, save_all=True, append_images=[puzzle_img])
        st.download_button(
            "Download Both Pages PDF",
            data=pdf_buf.getvalue(),
            file_name="mosaic_pages.pdf",
            mime="application/pdf"
        )
