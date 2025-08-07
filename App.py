import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from io import BytesIO

# Constants for page size at 300 DPI (8.5 x 11 inches)
PAGE_W, PAGE_H = 2550, 3300

def get_font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def generate_mosaic(im, grid_cols, max_colors, draw_grid_lines=True):
    cell_w = PAGE_W // grid_cols
    grid_w_px = cell_w * grid_cols
    grid_rows = PAGE_H // cell_w
    grid_h_px = cell_w * grid_rows

    im.thumbnail((grid_w_px, grid_h_px), Image.LANCZOS)
    canvas = Image.new("RGB", (grid_w_px, grid_h_px), (255,255,255))
    ox = (grid_w_px - im.width)//2
    oy = (grid_h_px - im.height)//2
    canvas.paste(im, (ox, oy))

    small = canvas.resize((grid_cols, grid_rows), Image.LANCZOS)

    pal = small.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
    pal_rgb = pal.convert("RGB")

    arr = np.array(pal_rgb)
    indices = np.array(pal)

    unique_idx, inverse = np.unique(indices.flatten(), return_inverse=True)
    colors = []
    for i in unique_idx:
        yx = np.argwhere(indices==i)[0]
        colors.append(tuple(arr[yx[0], yx[1]]))

    index_to_number = {int(old): idx+1 for idx, old in enumerate(unique_idx)}
    numbered_grid = np.vectorize(lambda v: index_to_number[int(v)])(indices)

    # Create answer image
    answer = Image.new("RGB", (PAGE_W, PAGE_H), (255,255,255))
    mosaic = Image.new("RGB", (grid_w_px, grid_h_px), (255,255,255))
    draw_m = ImageDraw.Draw(mosaic)

    for r in range(grid_rows):
        for c in range(grid_cols):
            num = numbered_grid[r, c]
            color = colors[num-1]
            x0 = c*cell_w
            y0 = r*cell_w
            draw_m.rectangle([x0, y0, x0+cell_w-1, y0+cell_w-1], fill=tuple(color))

    ax = (PAGE_W - grid_w_px)//2
    ay = (PAGE_H - grid_h_px)//2
    answer.paste(mosaic, (ax, ay))

    if draw_grid_lines:
        draw_a = ImageDraw.Draw(answer)
        for r in range(grid_rows+1):
            y = ay + r*cell_w
            draw_a.line([ax, y, ax+grid_w_px-1, y], fill=(0,0,0), width=1)
        for c in range(grid_cols+1):
            x = ax + c*cell_w
            draw_a.line([x, ay, x, ay+grid_h_px-1], fill=(0,0,0), width=1)

    # Create puzzle (numbered) image
    puzzle = Image.new("RGB", (PAGE_W, PAGE_H), (255,255,255))
    draw_p = ImageDraw.Draw(puzzle)

    for r in range(grid_rows):
        for c in range(grid_cols):
            x0 = ax + c*cell_w
            y0 = ay + r*cell_w
            draw_p.rectangle([x0, y0, x0+cell_w-1, y0+cell_w-1], outline=(0,0,0), width=1)

    # Draw legend
    legend_w = 300
    full_puzzle = Image.new("RGB", (PAGE_W, PAGE_H), (255,255,255))
    full_puzzle.paste(puzzle, (0,0))
    draw_lp = ImageDraw.Draw(full_puzzle)

    sw_x = PAGE_W - legend_w + 20
    sw_y = 120
    sw_s = 36
    font = get_font(max(12, cell_w//2))
    title_font = get_font(36)
    draw_lp.text((sw_x, 40), "Color Key", font=title_font, fill=(0,0,0))

    for i, col in enumerate(colors):
        y = sw_y + i*(sw_s+12)
        draw_lp.rectangle([sw_x, y, sw_x+sw_s, y+sw_s], fill=tuple(col), outline=(0,0,0))
        draw_lp.text((sw_x+sw_s+12, y+4), str(i+1), font=font, fill=(0,0,0))

    # Add numbers inside cells
    num_font = get_font(cell_w//2 if cell_w//2>10 else 12)
    dp = ImageDraw.Draw(full_puzzle)
    for r in range(grid_rows):
        for c in range(grid_cols):
            num = int(numbered_grid[r, c])
            x0 = ax + c*cell_w
            y0 = ay + r*cell_w
            txt = str(num)
            w, h = dp.textsize(txt, font=num_font)
            tx = x0 + (cell_w - w)/2
            ty = y0 + (cell_w - h)/2 - 2
            dp.text((tx, ty), txt, font=num_font, fill=(0,0,0))

    return full_puzzle, answer

def pil_to_bytes(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

st.title("🧩 Mystery Mosaic Color-by-Number Generator")

uploaded_file = st.file_uploader("Upload an image", type=["png","jpg","jpeg"])

grid_cols = st.slider("Grid Columns (puzzle complexity)", 30, 80, 60)
max_colors = st.slider("Max Colors (palette size)", 5, 30, 20)

if uploaded_file:
    im = Image.open(uploaded_file).convert("RGB")

    with st.spinner("Generating mosaic..."):
        puzzle_img, solution_img = generate_mosaic(im, grid_cols, max_colors)

    col1, col2 = st.columns(2)

    with col1:
        st.header("Puzzle Page")
        st.image(puzzle_img, use_column_width=True)
        buf = BytesIO()
        puzzle_img.save(buf, format="PNG")
        st.download_button("Download Puzzle PNG", buf.getvalue(), file_name="puzzle.png", mime="image/png")

    with col2:
        st.header("Solution Page")
        st.image(solution_img, use_column_width=True)
        buf = BytesIO()
        solution_img.save(buf, format="PNG")
        st.download_button("Download Solution PNG", buf.getvalue(), file_name="solution.png", mime="image/png")
else:
    st.info("Upload an image to start generating your mystery mosaic color-by-number pages.")
