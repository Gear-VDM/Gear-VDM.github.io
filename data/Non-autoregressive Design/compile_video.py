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
good_examples = [20, 22, 35, 40, 44, 4, 58, 87, 95, 99, 9]
examples = []
base_path = "/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Gen_20/Gear_Gen_Normalize_Uncond_HighNoise_SCRATCH_DefaultWeight_12000_UncondLowSCRATCHOnesidedWeight_12000_shift1_1.0_step32b/"
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
                ("Driving Gear (Condition)", os.path.join(vis_path, "vis", f"{g}_loop_0_input_modality_0.mp4")),
                ("Generated", os.path.join(base_path, "results", f"{g}_loop_{loop}_modality_0.mp4")),
                ("Generated (w/ parsed results)", os.path.join(base_path, "parsed", f"{g}_loop_0_modality_0", "normalized_coordinate_gear_overlay.mp4"))
            ]
        lis.append([example])
    examples.append(lis)

BASE_FPS = 15
SPEED_FACTOR = 2.0  # >1.0 speeds up, <1.0 slows down
SEQUENCE_BY_ROW = True  # Treat list-of-rows as a sequential series

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
            "Generated (w/ parsed results)": (255, 0, 0)    # Red border
        }
        
        # Pass the border_colors argument to the stacker
        if len(grid_sequence) == 1:
            stack_videos.stack_videos(
                grid_sequence[0],
                output_path,
                border_colors=border_cfg,
                target_fps=target_fps,
            )
            return output_path

        temp_paths = []
        base, _ = os.path.splitext(output_path)
        for seq_idx, grid in enumerate(grid_sequence):
            temp_path = f"{base}_part{seq_idx:03d}.mp4"
            stack_videos.stack_videos(
                grid,
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
    output_dir = "./../../video/Non-autoregressive Design/"
    os.makedirs(output_dir, exist_ok=True)

    for idx, example in tqdm(enumerate(examples), desc="Processing Examples"):
        visualize(example, output_path = os.path.join(output_dir, f"{idx}.mp4"))