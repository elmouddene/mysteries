import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# ===================== FIXED PALETTE =====================
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

# ===================== COLOR MATCHING =====================
def closest_palette_color(rgb):
    return min(PALETTE.items(), key=lambda c: np.linalg.norm(np.array(rgb)-np.array(c[1])))[0]

def generate_mosaic_pages(image, grid_cols):
    DPI = 300
    WIDTH_INCHES, HEIGHT_INCHES = 8.5, 11
    WIDTH_PX, HEIGHT_PX = int(WIDTH_INCHES * DPI), int(HEIGHT_INCHES * DPI)

    img = image.convert("RGB").resize((grid_cols, int(grid_cols * HEIGHT_INCHES / WIDTH_INCHES)), Image.Resampling.LANCZOS)
    img_np = np.array(img)

    # Quantize to fixed palette
    code_grid = []
    used_colors = set()
    for row in img_np:
        code_row = []
        for pixel in row:
            code = closest_palette_color(tuple(pixel))
            code_row.append(code)
            used_colors.add(code)
        code_grid.append(code_row)

    grid_rows = len(code_grid)
    cell_w, cell_h = WIDTH_PX // grid_cols, HEIGHT_PX // grid_rows

    # Create puzzle page
    puzzle_img = Image.new("RGB", (WIDTH_PX, HEIGHT_PX), "white")
    draw_puz = ImageDraw.Draw(puzzle_img)
    font_size = min(cell_w, cell_h) // 2
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    for y, row in enumerate(code_grid):
        for x, code in enumerate(row):
            left, top = x * cell_w, y * cell_h
            right, bottom = left + cell_w, top + cell_h
            draw_puz.rectangle([left, top, right, bottom], outline="black", width=1)
            w, h = draw_puz.textsize(code, font=font)
            draw_puz.text((left + (cell_w - w) / 2, top + (cell_h - h) / 2), code, fill="black", font=font)

    # Add color key at bottom
    key_height = cell_h * 2
    key_img = Image.new("RGB", (WIDTH_PX, key_height), "white")
    draw_key = ImageDraw.Draw(key_img)
    swatch_size = key_height - 10
    for idx, code in enumerate(sorted(used_colors)):
        x_pos = idx * (swatch_size + 10) + 10
        draw_key.rectangle([x_pos, 5, x_pos + swatch_size, 5 + swatch_size], fill=PALETTE[code], outline="black")
        draw_key.text((x_pos + swatch_size + 5, 5), code, font=font, fill="black")

    # Stack puzzle & key
    final_puzzle = Image.new("RGB", (WIDTH_PX, HEIGHT_PX + key_height), "white")
    final_puzzle.paste(puzzle_img, (0, 0))
    final_puzzle.paste(key_img, (0, HEIGHT_PX))

    # Create solution page
    solution_img = Image.new("RGB", (WIDTH_PX, HEIGHT_PX), "white")
    draw_sol = ImageDraw.Draw(solution_img)
    for y, row in enumerate(code_grid):
        for x, code in enumerate(row):
            left, top = x * cell_w, y * cell_h
            right, bottom = left + cell_w, top + cell_h
            draw_sol.rectangle([left, top, right, bottom], fill=PALETTE[code], outline="black", width=1)

    return final_puzzle, solution_img

def pil_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300,300))
    return buf.getvalue()

# ===================== STREAMLIT UI =====================
st.set_page_config(page_title="Mystery Mosaic Generator", layout="wide")

st.title("🎨 Mystery Mosaic Color by Number Generator")
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
grid_cols = st.slider("Number of columns", min_value=20, max_value=150, value=60)

if uploaded_file:
    image = Image.open(uploaded_file)
    puzzle_img, solution_img = generate_mosaic_pages(image, grid_cols)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Puzzle Page")
        st.image(puzzle_img, use_container_width=True)
        st.download_button("Download Puzzle PNG", data=pil_to_bytes(puzzle_img), file_name="puzzle.png", mime="image/png")
    with col2:
        st.subheader("Solution Page")
        st.image(solution_img, use_container_width=True)
        st.download_button("Download Solution PNG", data=pil_to_bytes(solution_img), file_name="solution.png", mime="image/png")
