"""
Stack all your comparison videos into a 2x3 or 2x4 video grids with titles. 
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

def load_frames(path, max_frames):
    """
    Robustly loads frames. Handles static images and video files.
    """
    try:
        data = iio.imread(path, index=None)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return [np.zeros((480, 832, 3), dtype=np.uint8)]

    raw_frames = []

    if data.ndim == 3:
        raw_frames = [data]
    elif data.ndim == 4:
        raw_frames = list(data)
    elif data.ndim == 2:
        bgr = cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)
        raw_frames = [bgr]
    else:
        return [np.zeros((480, 832, 3), dtype=np.uint8)]

    output_frames = []
    source_len = len(raw_frames)
    
    for i in range(max_frames):
        frame = raw_frames[i % source_len]
        output_frames.append(frame)
        
    return output_frames

def stack_videos(data_dict, output_filename="grid_output.mp4", cols=4, border_colors=None):
    if len(data_dict) == 8:
        cols = 4
    if len(data_dict) == 6:
        cols = 3
    if len(data_dict) == 3:
        cols = 3
    TARGET_W = 832
    TARGET_H = 480
    TARGET_FPS = 15
    MAX_FRAMES = 49
    
    print(f"Processing {len(data_dict)} inputs...")
    
    processed_clips = []
    
    # 1. Pre-process clips
    for name, path in data_dict.items():
        raw_sequence = load_frames(path, MAX_FRAMES)
        processed_stream = []
        
        for frame in raw_sequence:
            res = crop_and_resize(frame, TARGET_W, TARGET_H)
            
            # Ensure array is fully contiguous before drawing to avoid OpenCV errors
            res = np.ascontiguousarray(res)
            
            # --- DRAW COLORED BORDERS ON THE VIDEO FRAME ONLY ---
            # border_colors maps a title substring to an RGB tuple. e.g. {"Source": (0, 0, 255)}
            if border_colors is not None:
                for key, color in border_colors.items():
                    if key in name:
                        border_thickness = 10 
                        cv2.rectangle(res, (0, 0), (res.shape[1]-1, res.shape[0]-1), color, border_thickness)
                        break # Only apply the first matched border configuration
            # ----------------------------------------------------

            # Add the text header AFTER drawing the border
            res = add_header(res, name)
            
            processed_stream.append(res)
            
        processed_clips.append(processed_stream)

    # 2. Initialize Writer
    try:
        writer = imageio.get_writer(output_filename, fps=TARGET_FPS, codec="libx264", pixelformat="yuv420p")
    except Exception:
        print("Warning: libx264/yuv420p not found, using default settings.")
        writer = imageio.get_writer(output_filename, fps=TARGET_FPS)

    # Calculate block size (frame + header)
    if processed_clips:
        block_h, block_w = processed_clips[0][0].shape[:2]
    else:
        block_h, block_w = 480+60, 832
        
    blank_block = np.full((block_h, block_w, 3), 0, dtype=np.uint8)

    print("Stitching frames...")
    
    for f_idx in range(MAX_FRAMES):
        current_frame_cells = []
        
        for clip in processed_clips:
            current_frame_cells.append(clip[f_idx])
            
        while len(current_frame_cells) % cols != 0:
            current_frame_cells.append(blank_block)
            
        grid_rows = []
        for i in range(0, len(current_frame_cells), cols):
            row_imgs = current_frame_cells[i:i+cols]
            grid_rows.append(np.hstack(row_imgs))
            
        final_frame = np.vstack(grid_rows)
        writer.append_data(final_frame)

    writer.close()
    print(f"Success! Saved to {output_filename}")

if __name__ == "__main__":
    # Put this in a loop to generate stacked videos for each sample
    inputs = {
        "Source video": "raw_videos/source.mp4",
        "ReCamMaster": "raw_videos/recam.mp4",
        "CamCloneMaster": "raw_videos/clone.mp4",
        "EX-4D": "raw_videos/ex4d.mp4",
        "Point cloud render": "raw_videos/pcd.mp4", 
        "TrajectoryCrafter": "raw_videos/traj.mp4",
        "GEN3C": "raw_videos/gen3c.mp4",
        "Vista4D (ours)": "raw_videos/ours.mp4"
    }

    # Example setup: Map title substrings to (R, G, B) tuples
    borders = {
        "Source video": (0, 0, 255),  # Blue
        "Vista4D": (255, 0, 0)        # Red
    }

    try:
        stack_videos(inputs, "videos/sample_name.mp4", cols=4, border_colors=borders)
    except Exception as e:
        print(f"An error occurred: {e}")