import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# ========================
# FIXED COLOR PALETTE (A-Z + 1-9)
# ========================
PALETTE = {
    "1": (0, 0, 0),          # Black
    "2": (64, 64, 64),       # Dark Gray
    "3": (192, 192, 192),    # Light Gray
    "4": (101, 67, 33),      # Dark Brown
    "5": (139, 69, 19),      # Brown
    "6": (205, 133, 63),     # Light Brown
    "7": (210, 180, 140),    # Tan
    "8": (255, 253, 208),    # Cream
    "9": (139, 0, 0),        # Dark Red
    "A": (255, 0, 0),        # Red
    "B": (255, 140, 0),      # Dark Orange
    "C": (255, 165, 0),      # Bright Orange
    "D": (255, 255, 0),      # Yellow
    "E": (173, 255, 47),     # Yellow Green
    "F": (128, 128, 0),      # Olive Green
    "G": (0, 128, 0),        # Green
    "H": (127, 255, 212),    # Aqua Green
    "I": (0, 100, 0),        # Dark Green
    "J": (0, 0, 139),        # Dark Blue
    "K": (0, 0, 255),        # Blue
    "L": (135, 206, 235),    # Sky Blue
    "M": (173, 216, 230),    # Light Blue
    "N": (128, 0, 128),      # Purple
    "O": (148, 0, 211),      # Violet
    "P": (255, 0, 255),      # Magenta
    "Q": (230, 230, 250),    # Lavender
    "R": (231, 84, 128),     # Dark Pink
    "S": (255, 192, 203)     # Pink
}

# ========================
# FUNCTION: Find nearest palette color
# ========================
def closest_palette_color(rgb):
    return min(PALETTE.keys(),
               key=lambda k: np.linalg.norm(np.array(PALETTE[k]) - np.array(rgb)))

# ========================
# FUNCTION: Generate puzzle & solution
# ========================
def generate_mosaic_pages(img, grid_cols):
    DPI = 300
    WIDTH_INCH, HEIGHT_INCH = 8.5, 11
    WIDTH_PX, HEIGHT_PX = int(WIDTH_INCH * DPI), int(HEIGHT_INCH * DPI)

    # Resize image to fit exactly in grid
    cell_size = WIDTH_PX // grid_cols
    grid_rows = HEIGHT_PX // cell_size
    resized_img = img.resize((grid_cols, grid_rows), Image.NEAREST)

    # Prepare outputs
    puzzle_img = Image.new("RGB", (grid_cols * cell_size, grid_rows * cell_size), "white")
    solution_img = Image.new("RGB", (grid_cols * cell_size, grid_rows * cell_size), "white")
    draw_puz = ImageDraw.Draw(puzzle_img)
    draw_sol = ImageDraw.Draw(solution_img)

    # Font for numbers
    try:
        font = ImageFont.truetype("arial.ttf", int(cell_size * 0.5))
    except:
        font = ImageFont.load_default()

    used_colors = {}

    # Loop through cells
    for y in range(grid_rows):
        for x in range(grid_cols):
            rgb = resized_img.getpixel((x, y))
            code = closest_palette_color(rgb)
            used_colors[code] = PALETTE[code]

            # Draw solution cell
            draw_sol.rectangle([x * cell_size, y * cell_size,
                                (x + 1) * cell_size, (y + 1) * cell_size],
                               fill=PALETTE[code])

            # Draw puzzle cell (outline + number)
            draw_puz.rectangle([x * cell_size, y * cell_size,
                                (x + 1) * cell_size, (y + 1) * cell_size],
                               outline="black", width=1)

            bbox = draw_puz.textbbox((0, 0), code, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw_puz.text((x * cell_size + (cell_size - tw) / 2,
                           y * cell_size + (cell_size - th) / 2),
                          code, fill="black", font=font)

    # Generate color key
    key_height = int(len(used_colors) * (cell_size * 1.2))
    key_img = Image.new("RGB", (WIDTH_PX, key_height), "white")
    draw_key = ImageDraw.Draw(key_img)

    for i, (code, color) in enumerate(sorted(used_colors.items())):
        y_pos = i * int(cell_size * 1.2)
        draw_key.rectangle([10, y_pos, 10 + cell_size, y_pos + cell_size],
                           fill=color, outline="black")
        draw_key.text((20 + cell_size, y_pos + cell_size / 4),
                      f"{code} - RGB{color}", fill="black", font=font)

    return puzzle_img, solution_img, key_img

# ========================
# STREAMLIT UI
# ========================
st.set_page_config(page_title="Mystery Mosaic Generator", layout="wide")
st.title("🎨 Mystery Mosaic Color-by-Number Generator")

uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
grid_cols = st.slider("Grid Columns", min_value=20, max_value=200, value=80, step=5)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    puzzle_img, solution_img, key_img = generate_mosaic_pages(image, grid_cols)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Puzzle Page")
        st.image(puzzle_img, use_container_width=True)
        st.subheader("Color Key")
        st.image(key_img, use_container_width=True)
    with col2:
        st.subheader("Solution Page")
        st.image(solution_img, use_container_width=True)

    # Download buttons
    buf_puz = io.BytesIO()
    puzzle_img.save(buf_puz, format="PNG")
    st.download_button("Download Puzzle PNG", buf_puz.getvalue(), "puzzle.png", "image/png")

    buf_sol = io.BytesIO()
    solution_img.save(buf_sol, format="PNG")
    st.download_button("Download Solution PNG", buf_sol.getvalue(), "solution.png", "image/png")

    buf_key = io.BytesIO()
    key_img.save(buf_key, format="PNG")
    st.download_button("Download Color Key PNG", buf_key.getvalue(), "colorkey.png", "image/png")
