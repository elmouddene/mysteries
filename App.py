import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# Set up the page
st.set_page_config(page_title="Mystery Mosaic Generator", layout="wide")
st.title("🧩 Mystery Mosaic Color-by-Number Generator")

# Sidebar controls
uploaded_file = st.sidebar.file_uploader("Upload an Image", type=["png", "jpg", "jpeg"])
grid_cols = st.sidebar.slider("Grid Columns", min_value=10, max_value=100, value=40)
shape_type = st.sidebar.selectbox("Shape Type (Currently only Squares supported)", ["Squares"], index=0)

# Fixed color palette (RGB values)
fixed_palette = {
    '1': (0, 0, 0),               # Black
    '2': (64, 64, 64),            # Dark Gray
    '3': (160, 160, 160),         # Light Gray
    '4': (60, 40, 20),            # Dark Brown
    '5': (101, 67, 33),           # Brown
    '6': (181, 101, 29),          # Light Brown
    '7': (210, 180, 140),         # Tan
    '8': (255, 253, 208),         # Cream
    '9': (139, 0, 0),             # Dark Red
    'A': (255, 0, 0),             # Red
    'B': (255, 85, 0),            # Dark Orange
    'C': (255, 165, 0),           # Bright Orange
    'D': (255, 255, 0),           # Yellow
    'E': (173, 255, 47),          # Yellow Green
    'F': (128, 128, 0),           # Olive Green
    'G': (0, 128, 0),             # Green
    'H': (102, 205, 170),         # Aqua Green
    'I': (0, 100, 0),             # Dark Green
    'J': (0, 0, 139),             # Dark Blue
    'K': (0, 0, 255),             # Blue
    'L': (135, 206, 235),         # Sky Blue
    'M': (173, 216, 230),         # Light Blue
    'N': (128, 0, 128),           # Purple
    'O': (148, 0, 211),           # Violet
    'P': (255, 0, 255),           # Magenta
    'Q': (230, 230, 250),         # Lavender
    'R': (231, 84, 128),          # Dark Pink
    'S': (255, 192, 203),         # Pink
}

palette_colors = list(fixed_palette.values())
label_lookup = {v: k for k, v in fixed_palette.items()}


def find_closest_color(rgb):
    r1, g1, b1 = rgb
    min_dist = float('inf')
    closest = None
    for color in palette_colors:
        r2, g2, b2 = color
        dist = (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2
        if dist < min_dist:
            min_dist = dist
            closest = color
    return closest


def process_image(image, cols):
    img = image.convert("RGB")
    width, height = img.size
    aspect_ratio = height / width
    new_width = cols
    new_height = int(aspect_ratio * new_width)
    resized = img.resize((new_width, new_height), Image.NEAREST)

    # Map to fixed color palette
    pixel_data = np.array(resized)
    quantized_pixels = np.zeros_like(pixel_data)

    for y in range(new_height):
        for x in range(new_width):
            original = tuple(pixel_data[y, x])
            closest = find_closest_color(original)
            quantized_pixels[y, x] = closest

    quantized_img = Image.fromarray(quantized_pixels.astype('uint8'))
    return quantized_img, new_width, new_height


def generate_mosaic(image, cols):
    mosaic_img, grid_width, grid_height = process_image(image, cols)
    pixels = np.array(mosaic_img)

    cell_size = 30
    margin = 20
    width = grid_width * cell_size + margin * 2
    height = grid_height * cell_size + margin * 2

    puzzle_img = Image.new("RGB", (width, height), color="white")
    solution_img = Image.new("RGB", (width, height), color="white")

    dp = ImageDraw.Draw(puzzle_img)
    ds = ImageDraw.Draw(solution_img)

    try:
        num_font = ImageFont.truetype("arial.ttf", size=cell_size // 2)
    except:
        num_font = ImageFont.load_default()

    for y in range(grid_height):
        for x in range(grid_width):
            color = tuple(pixels[y, x])
            label = label_lookup[color]

            top_left = (margin + x * cell_size, margin + y * cell_size)
            bottom_right = (top_left[0] + cell_size, top_left[1] + cell_size)

            # Puzzle (text only)
            dp.rectangle([top_left, bottom_right], outline="black", fill="white")
            bbox = dp.textbbox((0, 0), label, font=num_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            center_x = (top_left[0] + bottom_right[0]) / 2
            center_y = (top_left[1] + bottom_right[1]) / 2
            dp.text((center_x - w / 2, center_y - h / 2), label, fill="black", font=num_font)

            # Solution (color fill)
            ds.rectangle([top_left, bottom_right], fill=color, outline=None)

    return puzzle_img, solution_img


# Main app
if uploaded_file:
    im = Image.open(uploaded_file)
    puzzle_img, solution_img = generate_mosaic(im, grid_cols)

    st.subheader("Preview")
    col1, col2 = st.columns(2)
    with col1:
        st.image(puzzle_img, caption="Puzzle Page", use_column_width=True)
    with col2:
        st.image(solution_img, caption="Solution Page", use_column_width=True)

    # Download buttons
    buf1 = io.BytesIO()
    puzzle_img.save(buf1, format="PNG")
    st.download_button("Download Puzzle PNG", buf1.getvalue(), file_name="puzzle.png", mime="image/png")

    buf2 = io.BytesIO()
    solution_img.save(buf2, format="PNG")
    st.download_button("Download Solution PNG", buf2.getvalue(), file_name="solution.png", mime="image/png")
else:
    st.info("Upload an image from the sidebar to get started.")
