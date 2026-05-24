"""
Stack comparison videos into a titled grid.
"""

import cv2
import imageio.v3 as iio  # For reading
import imageio            # For writing
import numpy as np
from PIL import Image, ImageDraw, ImageFont # Added for better text support

def crop_and_resize(img, target_w=832, target_h=480):
    """
    Center-crops image to target aspect ratio, then resizes to target dimensions.
    """
    if img is None or img.size == 0:
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    h, w = img.shape[:2]
    target_ar = target_w / target_h
    current_ar = w / h

    if current_ar > target_ar:
        # Too wide: Crop width
        new_w = int(h * target_ar)
        start_x = (w - new_w) // 2
        img_cropped = img[:, start_x:start_x+new_w]
    else:
        # Too tall: Crop height
        new_h = int(w / target_ar)
        start_y = (h - new_h) // 2
        img_cropped = img[start_y:start_y+new_h, :]

    try:
        img_resized = cv2.resize(img_cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)
    except cv2.error:
        img_resized = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
    return img_resized

def add_header(img, text):
    """
    Adds a white header with centered black text using PIL for specific fonts.
    """
    h, w = img.shape[:2]
    header_h = 64  # Increased height for larger text
    font_size = 50 # Increased font size (approx 1.5x)

    # Create white background for header
    header_bg = Image.new('RGB', (w, header_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(header_bg)

    # Try loading Arial or Times New Roman, fallback to default
    try:
        # Common names for Windows/Linux/Mac
        font_names = ["arial.ttf", "Arial.ttf", "times.ttf", "Times New Roman.ttf", "DejaVuSans.ttf"]
        font = None
        for name in font_names:
            try:
                font = ImageFont.truetype(name, font_size)
                break
            except IOError:
                continue
        if font is None:
            raise IOError("No specific fonts found")
    except IOError:
        font = ImageFont.load_default()
        print("Warning: specific font not found, using default.")

    # Calculate centered position
    # bbox = (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (w - text_w) / 2
    y = (header_h - text_h) / 2 - 4 # Slight offset for baseline

    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    # Convert PIL header back to Numpy
    header_np = np.array(header_bg)

    # Stack vertically
    return np.vstack((header_np, img))

def normalize_frame(frame):
    if frame is None or frame.size == 0:
        return None

    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    elif frame.ndim == 3 and frame.shape[2] == 4:
        frame = frame[:, :, :3]
    elif frame.ndim != 3 or frame.shape[2] != 3:
        return None

    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255)
        if frame.max() <= 1.0:
            frame = frame * 255.0
        frame = frame.astype(np.uint8)

    return frame

def load_media(path, fallback_shape):
    """
    Loads all frames from a video or a single image.
    Returns (frames, is_static).
    """
    blank = np.zeros(fallback_shape, dtype=np.uint8)

    if path is None or path == "":
        return [blank], True

    try:
        data = iio.imread(path, index=None)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return [blank], True

    if data.ndim == 2:
        frame = normalize_frame(data)
        return [frame if frame is not None else blank], True

    if data.ndim == 3:
        frame = normalize_frame(data)
        return [frame if frame is not None else blank], True

    if data.ndim == 4:
        frames = []
        for f in data:
            nf = normalize_frame(f)
            frames.append(nf if nf is not None else blank)
        if len(frames) == 0:
            return [blank], True
        return frames, False

    return [blank], True

def resample_frames(frames, target_len, is_static):
    if target_len <= 0:
        return []

    if not frames:
        return []

    if is_static or len(frames) <= 1:
        return [frames[0]] * target_len

    if target_len >= len(frames):
        return frames

    idxs = np.linspace(0, len(frames) - 1, target_len, dtype=int)
    return [frames[i] for i in idxs]

def stack_videos(data_grid, output_filename="grid_output.mp4", border_colors=None, target_fps=None):
    TARGET_W = 832
    TARGET_H = 480
    if target_fps is None or target_fps <= 0:
        target_fps = 15
    TARGET_FPS = target_fps
    DEFAULT_STATIC_SECONDS = 1
    DEFAULT_FRAME_SHAPE = (TARGET_H, TARGET_W, 3)

    if not data_grid:
        print("No inputs found. data_grid is empty.")
        return

    rows = len(data_grid)
    cols = max((len(row) for row in data_grid), default=0)
    if cols == 0:
        print("No inputs found. All rows are empty.")
        return
    total_inputs = sum(1 for row in data_grid for cell in row if cell is not None)
    print(f"Processing {total_inputs} inputs...")
    
    processed_clips = []
    
    clips_grid = []
    for row in data_grid:
        row_clips = []
        for col_idx in range(cols):
            if col_idx >= len(row) or row[col_idx] is None:
                row_clips.append(None)
                continue
            name, path = row[col_idx]
            frames, is_static = load_media(path, DEFAULT_FRAME_SHAPE)
            row_clips.append({
                "name": name,
                "frames": frames,
                "is_static": is_static,
            })
        clips_grid.append(row_clips)

    video_lengths = [
        len(cell["frames"])
        for row in clips_grid
        for cell in row
        if cell is not None and not cell["is_static"] and len(cell["frames"]) > 1
    ]

    if video_lengths:
        target_frames = min(video_lengths)
    else:
        target_frames = max(int(DEFAULT_STATIC_SECONDS * TARGET_FPS), 1)

    # 1. Pre-process clips
    for row in clips_grid:
        processed_row = []
        for cell in row:
            if cell is None:
                processed_row.append(None)
                continue

            raw_sequence = resample_frames(cell["frames"], target_frames, cell["is_static"])
            processed_stream = []

            for frame in raw_sequence:
                res = crop_and_resize(frame, TARGET_W, TARGET_H)

                # Ensure array is fully contiguous before drawing to avoid OpenCV errors
                res = np.ascontiguousarray(res)

                # --- DRAW COLORED BORDERS ON THE VIDEO FRAME ONLY ---
                # border_colors maps a title substring to an RGB tuple. e.g. {"Source": (0, 0, 255)}
                if border_colors is not None:
                    for key, color in border_colors.items():
                        if key in cell["name"]:
                            border_thickness = 10
                            cv2.rectangle(res, (0, 0), (res.shape[1]-1, res.shape[0]-1), color, border_thickness)
                            break # Only apply the first matched border configuration
                # ----------------------------------------------------

                # Add the text header AFTER drawing the border
                res = add_header(res, cell["name"])

                processed_stream.append(res)

            processed_row.append(processed_stream)
        processed_clips.append(processed_row)

    # 2. Initialize Writer
    try:
        writer = imageio.get_writer(output_filename, fps=TARGET_FPS, codec="libx264", pixelformat="yuv420p")
    except Exception:
        print("Warning: libx264/yuv420p not found, using default settings.")
        writer = imageio.get_writer(output_filename, fps=TARGET_FPS)

    # Calculate block size (frame + header)
    block_h, block_w = TARGET_H + 64, TARGET_W
    for row in processed_clips:
        for cell in row:
            if cell:
                block_h, block_w = cell[0].shape[:2]
                break
        if block_h != TARGET_H + 64 or block_w != TARGET_W:
            break

    blank_block = np.full((block_h, block_w, 3), 0, dtype=np.uint8)

    print("Stitching frames...")
    
    for f_idx in range(target_frames):
        grid_rows = []

        for row in processed_clips:
            current_row_cells = []
            for cell in row:
                if cell is None or f_idx >= len(cell):
                    current_row_cells.append(blank_block)
                else:
                    current_row_cells.append(cell[f_idx])

            while len(current_row_cells) < cols:
                current_row_cells.append(blank_block)

            grid_rows.append(np.hstack(current_row_cells))

        final_frame = np.vstack(grid_rows)
        writer.append_data(final_frame)

    writer.close()
    print(f"Success! Saved to {output_filename}")

if __name__ == "__main__":
    # Put this in a loop to generate stacked videos for each sample
    inputs = [
        [
            ("Source video", "raw_videos/source.mp4"),
            ("ReCamMaster", "raw_videos/recam.mp4"),
            ("CamCloneMaster", "raw_videos/clone.mp4"),
            ("EX-4D", "raw_videos/ex4d.mp4"),
        ],
        [
            ("Point cloud render", "raw_videos/pcd.mp4"),
            ("TrajectoryCrafter", "raw_videos/traj.mp4"),
            ("GEN3C", "raw_videos/gen3c.mp4"),
            ("Vista4D (ours)", "raw_videos/ours.mp4"),
        ]
    ]

    # Example setup: Map title substrings to (R, G, B) tuples
    borders = {
        "Source video": (0, 0, 255),  # Blue
        "Vista4D": (255, 0, 0)        # Red
    }

    try:
        stack_videos(inputs, "videos/sample_name.mp4", border_colors=borders)
    except Exception as e:
        print(f"An error occurred: {e}")