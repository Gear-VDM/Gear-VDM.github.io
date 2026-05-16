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
    from moviepy.editor import ColorClip
except ImportError:
    from moviepy.video.VideoClip import ColorClip

# Visualizer borrowed from reference code
try:
    from moviepy.editor import ImageSequenceClip
except ImportError:
    from moviepy.video.io.ImageSequenceClip import ImageSequenceClip


################### Do not modify ###############################
examples = [
                [[
                    ("First Frame (Condition)", "./0.png"),
                    ("Veo 3.1", "./0_veo31.mp4"),
                    ("Ray3.14", "./0_ray314.mp4")
                ]],
                [[
                    ("First Frame (Condition)", "./1.png"),
                    ("Veo 3.1", "./1_veo31.mp4"),
                    ("Ray3.14", "./1_ray314.mp4")
                ]],
                [[
                    ("First Frame (Condition)", "./2.jpg"),
                    ("Veo 3.1", "./2_veo31.mp4"),
                    ("Ray3.14", "./2_ray314.mp4")
                ]],
                [[
                    ("First Frame (Condition)", "./3.jpg"),
                    ("Veo 3.1", "./3_veo31.mp4"),
                    ("Ray3.14", "./3_ray314.mp4")
                ]],         
            ]
########################################################################################

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

def visualize(grid_inputs, output_path):
    if not grid_inputs:
        return None

    # Use Source Video for FPS/Duration, but FORCE Width/Height for visualizer
    fps = 15
        
    # FORCE RESOLUTION FOR TRACKS
    w, h = 832, 480

    # --- Step 5: Padding ---
    grid_cols = 2

    # --- Step 6: Stack Videos ---
    try:
        # --- NEW CODE: Define borders (RGB format) ---
        border_cfg = {
            "First Frame (Condition)": (0, 0, 255),      # Blue border
            "Veo 3.1": (255, 0, 0),   # Red border
            "Ray3.14": (255, 0, 0)    # Red border
        }
        
        # Pass the border_colors argument to the stacker
        stack_videos.stack_videos(grid_inputs, output_path, border_colors=border_cfg)
        # ---------------------------------------------
        
        return output_path
    except Exception as e:
        print(f"Error in stack_videos: {e}")
        return None

if __name__ == "__main__":
    output_dir = "./../../video/Animating Mechanical Systems with Off-the-Shelf Commercial Video Models/"
    os.makedirs(output_dir, exist_ok=True)

    for idx, example in tqdm(enumerate(examples), desc="Processing Examples"):
        visualize(example, output_path = os.path.join(output_dir, f"{idx}.mp4"))