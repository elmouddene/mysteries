import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# Set up the page
st.set_page_config(page_title="Mystery Mosaic Generator", layout="wide")
st.title("🧩 Mystery Mosaic Color-by-Number Generator")

# Sidebar controls
uploaded_file = st.sidebar.file_uploader("Upload an Image", type=["png", "jpg", "jpeg"])
grid_cols = st.sidebar.slider("Grid Columns", min_value=20, max_value=100, value=60)
max_colors = st.sidebar.slider("Max Colors", min_value=4, max_value=30, value=20)
shape_type = st.sidebar.selectbox("Shape Type (Currently only Squares supported)", ["Squares"], index=0)


# Function to quantize and pixelate image
def process_image(image, cols, max_colors):
    img = image.convert("RGB")
    width, height = img.size
    aspect_ratio = height / width
    new_width = cols
    new_height = int(aspect_ratio * new_width)

    img_small = img.resize((new_width, new_height), Image.BILINEAR)
    img_quantized = img_small.quantize(colors=max_colors, method=Image.MEDIANCUT)
    img_out = img_quantized.convert("RGB")
    return img_out, new_width, new_height


# Function to generate puzzle and solution pages
def generate_mosaic(image, cols, max_colors):
    mosaic_img, grid_cols, grid_rows = process_image(image, cols, max_colors)
    pixels = np.array(mosaic_img)

    # Create puzzle and solution images
    cell_size = 20
    margin = 20
    width = grid_cols * cell_size + margin * 2
    height = grid_rows * cell_size + margin * 2

    puzzle_img = Image.new("RGB", (width, height), color="white")
    solution_img = Image.new("RGB", (width, height), color="white")

    dp = ImageDraw.Draw(puzzle_img)
    ds = ImageDraw.Draw(solution_img)

    try:
        num_font = ImageFont.truetype("arial.ttf", size=cell_size // 2)
    except:
        num_font = ImageFont.load_default()

    color_map = {}
    color_index = 1

    for y in range(grid_rows):
        for x in range(grid_cols):
            color = tuple(pixels[y, x])
            if color not in color_map:
                color_map[color] = color_index
                color_index += 1

            index = color_map[color]
            top_left = (margin + x * cell_size, margin + y * cell_size)
            bottom_right = (top_left[0] + cell_size, top_left[1] + cell_size)

            # Draw puzzle square
            dp.rectangle([top_left, bottom_right], outline="black", fill="white")
            txt = str(index)
            bbox = dp.textbbox((0, 0), txt, font=num_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            center_x = (top_left[0] + bottom_right[0]) / 2
            center_y = (top_left[1] + bottom_right[1]) / 2
            dp.text((center_x - w / 2, center_y - h / 2), txt, fill="black", font=num_font)

            # Draw solution square
            ds.rectangle([top_left, bottom_right], fill=color, outline=None)

    return puzzle_img, solution_img


# Main logic
if uploaded_file:
    im = Image.open(uploaded_file)
    puzzle_img, solution_img = generate_mosaic(im, grid_cols, max_colors)

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

    # Optionally: Add PDF export here in the future
else:
    st.info("Upload an image from the sidebar to get started.")
