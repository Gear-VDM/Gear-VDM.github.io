"""
python compile_video.py
"""

import os
import sys
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib import cm
from tqdm import tqdm

sys.path.append("./../../")
import stack_videos
import concurrent.futures
import uuid

# Handle MoviePy for generating the white spacer video if needed
try:
    # Modern MoviePy (v2.x+) approach: everything is at the top level
    from moviepy import ColorClip, VideoFileClip, concatenate_videoclips
except ImportError:
    try:
        # Legacy MoviePy (v1.x) preferred approach
        from moviepy.editor import ColorClip, VideoFileClip, concatenate_videoclips
    except ImportError:
        # Legacy MoviePy (v1.x) explicit submodule fallback
        from moviepy.video.VideoClip import ColorClip
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips

# Visualizer borrowed from reference code
try:
    from moviepy.editor import ImageSequenceClip
except ImportError:
    from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

#################### Good examples ##############################
good_examples = [21, 37, 47]
examples = []
base_path = "/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Motion_20/Gear_Motion_Normalize_HighNoise_SCRATCH_7000_MotionLowSCRATCHOnesidedWeight_8000_shift1_1.0_step32b/"
vis_path = "/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Motion_20/Gear_Motion_Normalize_HighNoise_18500_MotionLow_18500_shift1_1.0_step32b/"

for g in good_examples:
    loop_max = 1
    lis = []
    for loop in range(loop_max + 1):
        if loop == loop_max:
            continue
            """
            example = [
                ("Driving Gear (Condition)", os.path.join(vis_path, "vis", f"{g}_loop_0_input_modality_0.mp4")),
                ("Generated (w/ parsed results)", os.path.join(base_path, "parsed", f"{g}_loop_0_modality_0", "normalized_coordinate_gear_overlay.mp4"))
            ]
            """
        else:
            example = [
                ("First Frame (Condition)", os.path.join(vis_path, "vis", f"{g}_loop_0_input_modality_0_reference.png")),
                ("Driving Gear (Condition)", os.path.join(vis_path, "vis", f"{g}_loop_0_input_modality_0.mp4")),
                #/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Motion_20/Gear_Motion_Normalize_HighNoise_18500_MotionLow_18500_shift1_1.0_step32b/parsed/46_loop_0_modality_0/normalized_coordinate_gear_overlay.mp4
                ("Generated (w/ parsed results)", os.path.join(base_path, "parsed", f"{g}_loop_0_modality_0", "normalized_coordinate_gear_overlay.mp4")),
                ("Kinematic Alignment Error", os.path.join(base_path, "parsed",  f"{g}_loop_0_modality_0", "debug_kinematic_tracking.png")),
            ]
        lis.append([example])
    examples.append(lis)

BASE_FPS = 15
SPEED_FACTOR = 2.0  # >1.0 speeds up, <1.0 slows down
SEQUENCE_BY_ROW = True  # Treat list-of-rows as a sequential series

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

def _is_video_path(path):
    if not isinstance(path, (str, os.PathLike)):
        return False
    return os.path.splitext(str(path))[1].lower() in VIDEO_EXTS

def _get_video_size(video_path):
    if not video_path or not os.path.exists(video_path):
        return None
    cap = cv2.VideoCapture(video_path)
    try:
        if not cap.isOpened():
            return None
        width = int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        if width > 0 and height > 0:
            return (width, height)
        ok, frame = cap.read()
        if ok and frame is not None and frame.size > 0:
            return (int(frame.shape[1]), int(frame.shape[0]))
    finally:
        cap.release()
    return None

def _pad_or_crop_to_size(img, target_w, target_h):
    if img is None or img.size == 0:
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]

    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    src_h, src_w = img.shape[:2]
    copy_w = min(src_w, target_w)
    copy_h = min(src_h, target_h)
    canvas[:copy_h, :copy_w] = img[:copy_h, :copy_w]
    return canvas

def _prepare_debug_kinematic_image(debug_path, ref_video_path, temp_dir):
    if not debug_path or not os.path.exists(debug_path):
        return debug_path
    if not ref_video_path or not os.path.exists(ref_video_path):
        return debug_path

    target_size = _get_video_size(ref_video_path)
    if target_size is None:
        return debug_path

    img = cv2.imread(debug_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return debug_path

    target_w, target_h = target_size
    padded = _pad_or_crop_to_size(img, target_w, target_h)

    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(debug_path))[0]
    temp_path = os.path.join(temp_dir, f"{base_name}_padded_{target_w}x{target_h}.png")
    cv2.imwrite(temp_path, padded)
    return temp_path

def _normalize_debug_images_for_grid(grid, output_path):
    if not grid:
        return grid

    temp_dir = os.path.join(os.path.dirname(output_path), "_tmp_debug_kinematic")
    normalized = []
    for row in grid:
        if not isinstance(row, list):
            normalized.append(row)
            continue
        ref_video_path = None
        for cell in row:
            if not _is_cell(cell):
                continue
            name, path = cell
            if name == "Generated (w/ parsed results)" and _is_video_path(path):
                ref_video_path = path
                break
        if ref_video_path is None:
            for cell in row:
                if not _is_cell(cell):
                    continue
                _, path = cell
                if _is_video_path(path):
                    ref_video_path = path
                    break

        new_row = []
        for cell in row:
            if not _is_cell(cell):
                new_row.append(cell)
                continue
            name, path = cell
            if name == "Kinematic Alignment Error":
                path = _prepare_debug_kinematic_image(path, ref_video_path, temp_dir)
            new_row.append((name, path))
        normalized.append(new_row)
    return normalized

def get_white_video(output_path, width=832, height=480, duration=1.0, fps=15):
    """Generates a white video to be used as padding."""
    if os.path.exists(output_path):
        return output_path
    
    try:
        clip = ColorClip(size=(width, height), color=(255, 255, 255), duration=duration)
        clip.write_videofile(output_path, codec="libx264", fps=fps, audio=False, logger=None)
        return output_path
    except Exception as e:
        print(f"Failed to create white video: {e}")
        return None

def _is_cell(obj):
    if not isinstance(obj, (tuple, list)) or len(obj) != 2:
        return False
    name, path = obj
    if not isinstance(name, str):
        return False
    return isinstance(path, (str, bytes, os.PathLike)) or path is None

def _is_row(obj):
    if not isinstance(obj, list):
        return False
    if len(obj) == 0:
        return True
    return _is_cell(obj[0])

def _is_grid(obj):
    if not isinstance(obj, list):
        return False
    if len(obj) == 0:
        return True
    return _is_row(obj[0])

def _collect_grids(obj, sequence_by_row=False):
    if _is_grid(obj):
        if sequence_by_row and len(obj) > 0:
            return [[row] for row in obj]
        return [obj]
    if isinstance(obj, list):
        grids = []
        for item in obj:
            grids.extend(_collect_grids(item, sequence_by_row=sequence_by_row))
        return grids
    return []

def concat_videos(input_paths, output_path, default_fps=15):
    if not input_paths:
        return None

    clips = []
    final_clip = None
    try:
        for path in input_paths:
            clips.append(VideoFileClip(path))

        fps = getattr(clips[0], "fps", None) or default_fps
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, codec="libx264", fps=fps, audio=False, logger=None)
        return output_path
    except Exception as e:
        print(f"Failed to concatenate videos: {e}")
        return None
    finally:
        if final_clip is not None:
            try:
                final_clip.close()
            except Exception:
                pass
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass

def visualize(grid_inputs, output_path):
    if not grid_inputs:
        return None

    grid_sequence = _collect_grids(grid_inputs, sequence_by_row=SEQUENCE_BY_ROW)
    if not grid_sequence:
        print("No valid grids found in inputs.")
        return None

    target_fps = max(BASE_FPS * SPEED_FACTOR, 1)

    # --- Step 6: Stack Videos ---
    try:
        # --- NEW CODE: Define borders (RGB format) ---
        border_cfg = {
            "First Frame (Condition)": (0, 0, 255),      # Blue border
            "Driving Gear (Condition)": (0, 0, 255),   # Blue border
            "Generated": (255, 0, 0), #Red border
            "Generated (w/ parsed results)": (255, 0, 0),    # Red border
            "Kinematic Alignment Error" : (255, 255, 0) # Yellow border
        }
        
        # Pass the border_colors argument to the stacker
        if len(grid_sequence) == 1:
            normalized_grid = _normalize_debug_images_for_grid(grid_sequence[0], output_path)
            stack_videos.stack_videos(
                normalized_grid,
                output_path,
                border_colors=border_cfg,
                target_fps=target_fps,
            )
            return output_path

        temp_paths = []
        base, _ = os.path.splitext(output_path)
        for seq_idx, grid in enumerate(grid_sequence):
            temp_path = f"{base}_part{seq_idx:03d}.mp4"
            normalized_grid = _normalize_debug_images_for_grid(grid, output_path)
            stack_videos.stack_videos(
                normalized_grid,
                temp_path,
                border_colors=border_cfg,
                target_fps=target_fps,
            )
            if not os.path.exists(temp_path):
                print(f"Missing segment output: {temp_path}")
                return None
            temp_paths.append(temp_path)

        concat_videos(temp_paths, output_path, default_fps=target_fps)

        for temp_path in temp_paths:
            try:
                os.remove(temp_path)
            except OSError:
                pass

        # ---------------------------------------------
        return output_path
    except Exception as e:
        print(f"Error in stack_videos: {e}")
        return None

if __name__ == "__main__":
    output_dir = "./../../video/Failure Cases of Non-autoregressive Simulation/"
    os.makedirs(output_dir, exist_ok=True)

    for idx, example in tqdm(enumerate(examples), desc="Processing Examples"):
        visualize(example, output_path = os.path.join(output_dir, f"{idx}.mp4"))