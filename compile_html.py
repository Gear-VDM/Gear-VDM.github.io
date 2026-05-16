"""
How to run:
    python compile_html.py --input_folder "./videos" 

Input:
./video/
    mesh/    
        0.mp4
        1.mp4
    ...
    {application_name}/
"""
import os
import glob
import json
import argparse
import urllib.parse

# --- CONFIGURATION ---

PAPER_TITLE = "Towards Designing and Simulating Mechanical Systems with Video Diffusion Models: A Study with 2D Gear Systems"

AUTHORS = [
    ("Anonymous Authors", [0]),
]

INSTITUTIONS = [
    "Anonymous Institutions", 
]

ARXIV_LINK = "https://arxiv.org/abs/20XX.XXXXX"
CODE_LINK = "https://github.com/username/repo"


ABSTRACT_TEXT = """
<p>
We investigate whether state-of-the-art video generators base on diffusion transformers can understand and generate accurately complex physical systems, using 2D involute gear trains as a testbed.
These mechanisms are conceptually simple and yet challenging to simulate as they require to capture accurately long cause-effect interactions, where a single driving gear dictates the rotational speed and orientation of the entire mechanism.
We develop a rigorous evaluation framework where generated videos are mapped to a formal representation of the underlying mechanism, which is then quantitatively tested for physical correctness.
We consider both simulation and design tasks.
We find that off-the-shelf video generative models fail to generate physically plausible gear videos at all, but that even light fine-tuning can simulate reasonably accurately up to 20 gears.
However, models do not generalise well beyond the number of gears seen during training.
For design, we find that naïvely fine-tuned models struggle to produce valid spatial layouts, often generating gears detached from others, but that modulating the training diffusion noise to spend more time in a `reasoning' phase of the generation process can significantly improve them.
</p>
"""

# --- 3-LEVEL HIERARCHY CONFIG ---
# The script automatically detects if an item is a "Group" (tuple with list) or "Single" (string)
SIDEBAR_CONFIG = [
    ("Supplemental Videos", [
        "Animating mechanical systems with commercial video models",
        "Results of non-autoregressive simulation (Sec 4)",
        "Results of autoregressive simulation (Sec 4)",
        "Results of non-autoregressive design (Sec 5)",
        "Results of autoregressive design (Sec 5)",
        "(Ablation) Results of non-autoregressive design with default time schedule",
        "(Ablation) Results of autoregressive design with default time schedule",
    ]),
]

"""
SIDEBAR_CONFIG = [
    ("Applications", [
        "Multi-Reference-driven Restylization",
        ("Mesh-driven Compositing", ["Keyframe-driven Mesh Stylization", 
                              "Multi-Reference-driven Mesh Compositing"]
        ),
        "Keypoint-driven Compositing",
        ("Static Scene Camera Control", [
            "Multi-Reference-driven Camera Control in Static Scene",
            "360° Camera Orbit in a Static Scene",
            #"Time Slice Effect"
        ]),
        "Camera Retargeting in Dynamic Scene",
        # Single item treated as Level 2 (No Level 3 children)
        ("Temporal Stabilization", [
            "Albedo",
            "Shading Estimates"
        ])
    ]),
    ("Baseline Comparison", [
        "First-Frame-driven Reconstruction",
        "First-Frame-driven Restylization",
    ]),
    ("Ablation Study", [
        ("Model Design",
         ["Ablation Study on Model Design",
          "PCA Analysis on Point-track Embeddings",
          ]
        ),
        ("Dataset",
         [
             "Dataset Visualization",
             "Ablation Study on Dataset",
         ]
        ),
        ("Reference Frames",
             [
                "Ablation Study on Keyframes",
                "Ablation Study on Non-keyframes",
             ]
        ),
        "Iterative Point-track Resampling",
    ])
]
"""

DATASET_DESCRIPTIONS = {
    # --- DATASETS (Bottom Level) ---
    "Ablation Study on Keyframes": "Unlike conventional point-track-conditioned image-to-video models that rely on the first frame, our model can be conditioned on arbitrary frames. As shown, it supports conditioning on the first, middle, or last frame of a video. Moreover, we achieve the best reconstruction performance by conditioning on four uniformly sampled reference frames.",
    "Ablation Study on Non-keyframes": "Beyond keyframe conditioning, our model can be guided by reference images that do not exactly correspond to any generated frame. As shown, the model effectively retrieves relevant visual information from reference images to produce coherent videos.",
    "Iterative Point-track Resampling" : "We provide a visual comparison of detected point-tracks obtained using our iterative resampling strategy (Appendix Algorithm 1) and uniform random sampling of point queries over the video frames. Our iterative resampling produces denser and more uniformly distributed point-tracks, achieving better spatial coverage with reduced sparsity.",
}

# --- HTML Template ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{paper_title}</title>
    <meta name="description" content="{paper_title}">
    
    <style>
        :root {{
            /* --- COLOR PALETTE --- */
            --primary-color: #0078d4;        
            --primary-hover: #005a9e;        
            --text-main: #333333;            
            --text-title: #222222;           
            --text-secondary: #555555;       
            --bg-sidebar: #f4f4f4;
            --bg-body: #ffffff;
            --border-color: #e0e0e0;
            --bg-section: #f4f4f4;
            --bg-level1: #e6f2fb; 
            
            /* Standard System Sans-Serif Stack */
            --font-stack: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }}

        body {{
            font-family: var(--font-stack);
            background-color: var(--bg-body);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            display: flex; 
            overflow-x: hidden;
        }}

        /* --- HIDE CLUSTRMAPS CONTAINER --- */
        #clustrmaps-widget-container {{
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            position: absolute;
            top: -9999px;
            left: -9999px;
        }}
        
        /* --- Sidebar --- */
        .dataset-nav {{
            position: fixed;
            top: 0;
            left: 0;
            width: 250px; 
            height: 100vh;
            background-color: var(--bg-sidebar);
            border-right: 1px solid #d0d0d0;
            padding-top: 60px; 
            padding-left: 0;
            padding-right: 0;
            z-index: 1002;
            display: flex;
            flex-direction: column; 
            gap: 2px; 
            overflow-y: auto; 
            overflow-x: hidden;
            box-sizing: border-box;
            transition: width 0.3s ease; 
        }}

        .dataset-nav::-webkit-scrollbar {{ width: 5px; }}
        .dataset-nav::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 4px; }}
        .dataset-nav::-webkit-scrollbar-track {{ background: transparent; }}

        .nav-category {{
            font-size: 11px;
            text-transform: none; 
            color: #777; 
            font-weight: 700;
            margin-top: 25px;
            margin-bottom: 5px;
            padding-left: 15px;
            letter-spacing: 0.5px;
            white-space: nowrap;
            transition: opacity 0.2s ease;
        }}
        
        .nav-subcategory {{
            font-size: 12px;
            color: #444;
            font-weight: 700;
            margin-top: 10px;
            margin-bottom: 2px;
            padding-left: 12px;
            text-transform: none;
        }}

        /* Base Sidebar Button */
        .dataset-btn {{
            background-color: transparent;
            color: #444;
            border: none;
            border-left: 4px solid transparent;
            cursor: pointer;
            text-align: left;
            word-break: break-word; 
            white-space: normal;    
            line-height: 1.4;        
            transition: all 0.2s ease;
            font-family: var(--font-stack);
            width: 100%;
            display: block;
            box-sizing: border-box;
        }}

        .dataset-btn:hover {{
            background-color: #e0e0e0;
            color: #000;
        }}

        .dataset-btn.active {{
            background-color: var(--bg-level1);
            color: #000;
            border-left-color: var(--primary-color);
            font-weight: 600;
        }}

        /* Overview Button */
        .dataset-btn.overview-btn {{
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 10px;
            font-size: 14px;
            padding: 8px 15px;
        }}

        /* Level 2 Button (Sub-Category) */
        .dataset-btn.level-2 {{
            font-size: 13px;
            font-weight: 600;
            padding: 8px 15px 8px 15px; 
            margin-top: 2px;
            color: #333;
        }}

        /* Level 3 Button (Content) */
        .dataset-btn.level-3 {{
            font-size: 12px;
            font-weight: 400;
            padding: 6px 15px 6px 30px; /* Indented */
            color: #555;
        }}
        
        .dataset-btn.level-3.active {{
             background-color: #f0f8ff; 
             color: var(--primary-color);
        }}

        /* --- Toggle Button --- */
        #sidebar-toggle {{
            position: fixed;
            top: 10px;
            left: 5px; 
            z-index: 1003;
            background-color: #fff;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
            line-height: 1;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: left 0.3s ease;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }}
        #sidebar-toggle:hover {{
            background-color: #f0f0f0;
        }}

        /* --- Main Content --- */
        .main-content {{
            margin-left: 250px;
            width: calc(100% - 250px); 
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: margin-left 0.3s ease, width 0.3s ease;
            box-sizing: border-box; 
        }}

        .paper-header {{
            width: 100%;
            background-color: #ffffff;
            padding: 50px 20px 30px 20px;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 40px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }}

        .paper-title {{
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 2.2rem;
            font-weight: 400; 
            color: #444; 
            margin: 0 auto 20px auto;
            line-height: 1.3;
            max-width: 900px;
            letter-spacing: -0.2px; 
        }}

        .paper-authors, .paper-institutions {{
            font-size: 1.2rem;
            color: #222;
            margin-bottom: 10px;
            font-weight: 500;
        }}
        .paper-institutions {{ font-size: 1rem; color: #666; margin-bottom: 20px; font-weight: 400; }}
        .author-span, .institution-span {{ margin: 0 10px; display: inline-block; }}
        sup {{ font-size: 0.7em; vertical-align: super; margin-left: 2px; color: var(--primary-color); }}

        .link-buttons {{ display: flex; justify-content: center; gap: 15px; margin-top: 15px; flex-wrap: wrap; }}
        .link-btn {{ background-color: #333; color: #fff; padding: 10px 24px; border-radius: 50px; text-decoration: none; font-weight: 600; font-size: 14px; transition: background-color 0.2s, transform 0.2s; display: inline-flex; align-items: center; gap: 8px; }}
        .link-btn:hover {{ background-color: #555; transform: translateY(-2px); }}
        .link-icon {{ width: 16px; height: 16px; fill: currentColor; }}

        .paper-footer {{ width: 100%; background-color: #fafafa; border-top: 1px solid var(--border-color); padding: 40px 20px; margin-top: 80px; text-align: center; }}
        .citation-block {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 15px; text-align: left; font-family: 'Consolas', monospace; font-size: 13px; color: #555; max-width: 800px; margin: 20px auto; overflow-x: auto; white-space: pre; }}

        .back-btn {{
            position: fixed; bottom: 30px; right: 30px; z-index: 2000;
            background-color: #222; color: white; border: none; padding: 12px 24px;
            border-radius: 50px; font-size: 14px; font-family: var(--font-stack);
            font-weight: 600; cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s, background-color 0.2s; display: none; 
            align-items: center; gap: 8px; letter-spacing: 0.3px;
        }}
        .back-btn:hover {{ transform: translateY(-2px); background-color: #000; box-shadow: 0 8px 25px rgba(0,0,0,0.25); }}

        /* --- Page & Dataset Styles --- */
        .content-block {{ margin-bottom: 80px; width: 100%; display: flex; flex-direction: column; align-items: center; scroll-margin-top: 80px; gap: 40px; }}
        
        h2.dataset-title {{ font-family: var(--font-stack); font-size: 1.6rem; font-weight: 400; color: var(--text-title); margin-bottom: 15px; border-bottom: 3px solid var(--primary-color); padding-bottom: 8px; display: inline-block; }}
        h3.content-subtitle {{ font-size: 1.4rem; color: #444; margin-top: 0; margin-bottom: 10px; font-weight: 600; }}
        .dataset-description {{ font-size: 1.05rem; color: var(--text-secondary); max-width: 800px; text-align: left; line-height: 1.7; margin: 0 auto 30px auto; padding: 0 20px; }}

        /* --- Overview Styling --- */
        .overview-container {{ width: 98%; max-width: 1600px; padding: 0 20px 100px 20px; display: none; box-sizing: border-box; margin: 0 auto; }}
        
        .abstract-section {{ max-width: 900px; margin: 0 auto 60px auto; text-align: justify; background-color: #ffffff; padding: 30px 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid #f0f0f0; }}
        .abstract-title {{ text-align: center; font-weight: 700; font-size: 1.2rem; text-transform: uppercase; color: #444; margin-bottom: 15px; letter-spacing: 1px; }}
        .abstract-content {{ font-size: 1.05rem; line-height: 1.8; color: #333; }}

        /* === HIERARCHY STYLES (UPDATED) === */
        
        /* Base styles for Level 1 & 2 Headers */
        .hierarchy-bar {{
            width: 100%;
            text-align: center; 
            padding: 15px 0; 
            border-radius: 6px;
            font-family: var(--font-stack);
            margin-bottom: 30px;
            text-transform: none; 
            letter-spacing: 1px;
            font-weight: 600;
        }}

        /* LEVEL 1: Lighter Blue Shadow, Blue Border, Larger */
        .level-1-header {{
            font-size: 1.5rem;
            margin-top: 60px;
            background-color: var(--bg-level1); /* Solid Light Blue Color */
            color: var(--primary-color);
            box-shadow: none; 
            border-left: 5px solid var(--primary-color);
            border-top: none;
        }}

        /* LEVEL 2: Gray Shadow, Blue Border, Smaller */
        .level-2-header {{
            font-size: 1.25rem;
            margin-top: 30px;
            background-color: #f9f9f9;
            color: #444; 
            box-shadow: none; 
            border: 1px solid #eee;
            border-left: 5px solid var(--primary-color);
        }}

        /* LEVEL 3: Underscore Style (Content Title) */
        .level-3-header {{
            font-family: var(--font-stack);
            font-size: 1.3rem; 
            color: #222; 
            margin: 0;
            font-weight: 600;
            display: inline-block;
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 6px;
        }}

        .overview-section {{ margin-bottom: 90px; width: 98%; max-width: 1600px; margin-left: auto; margin-right: auto; padding: 0 20px; box-sizing: border-box; scroll-margin-top: 80px; }}
        .overview-section-header {{ text-align: center; margin-bottom: 20px; }}
        .overview-desc {{ font-size: 1rem; color: var(--text-secondary); margin: 0 auto 30px auto; line-height: 1.6; max-width: 900px; text-align: left; }}
        .overview-action {{ text-align: center; margin-top: 30px; }}

        /* Carousel */
        .carousel-wrapper {{ position: relative; width: 100%; background: #000; border-radius: 8px; overflow: hidden; box-shadow: 0 6px 15px rgba(0,0,0,0.15); }}
        .carousel-wrapper video {{ width: 100%; display: block; height: auto; }}
        .carousel-btn {{ position: absolute; top: 50%; transform: translateY(-50%); background-color: rgba(0, 0, 0, 0.5); color: white; border: none; width: 50px; height: 50px; border-radius: 50%; cursor: pointer; z-index: 10; display: flex; align-items: center; justify-content: center; font-size: 24px; transition: background-color 0.2s; opacity: 0; }}
        .carousel-wrapper:hover .carousel-btn {{ opacity: 1; }}
        .carousel-btn:hover {{ background-color: rgba(0, 0, 0, 0.8); }}
        .carousel-btn.left {{ left: 20px; }}
        .carousel-btn.right {{ right: 20px; }}
        .slide-counter {{ position: absolute; bottom: 20px; right: 20px; background-color: rgba(0,0,0,0.6); color: white; padding: 5px 10px; border-radius: 4px; font-size: 13px; pointer-events: none; font-weight: 600; }}
        .carousel-dots {{
            display: flex;
            justify-content: center;
            gap: 6px;
            margin-top: 12px;
            padding: 4px 6px;
            overflow-x: auto;
            overflow-y: hidden;
            scrollbar-width: thin;
            scrollbar-color: #8fbce6 transparent;
            white-space: nowrap;
        }}
        .carousel-dots::-webkit-scrollbar {{ height: 6px; }}
        .carousel-dots::-webkit-scrollbar-thumb {{ background: #8fbce6; border-radius: 999px; }}
        .carousel-dots::-webkit-scrollbar-track {{ background: transparent; }}
        .carousel-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #d7ebfb;
            cursor: pointer;
            flex: 0 0 auto;
            padding: 0;
            border: none;
        }}
        .carousel-dot:hover {{ background: #b8daf5; }}
        .carousel-dot.active {{
            background: var(--primary-color);
            transform: scale(1.15);
        }}

        .btn-view-all {{ background-color: var(--primary-color); color: #fff; border: 2px solid var(--primary-color); padding: 10px 30px; border-radius: 50px; cursor: pointer; font-size: 13px; font-weight: 700; text-decoration: none; transition: all 0.2s; text-transform: uppercase; font-family: var(--font-stack); display: inline-block; letter-spacing: 0.5px; }}
        .btn-view-all:hover {{ background-color: var(--primary-hover); border-color: var(--primary-hover); color: white; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.15); }}

        /* Cards */
        .container {{ display: flex; flex-direction: column; align-items: center; gap: 50px; padding-bottom: 100px; width: 98%; max-width: 1600px; box-sizing: border-box; padding-top: 20px; }}
        .card {{ background-color: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; border: 1px solid #e0e0e0; display: block; transition: transform 0.2s ease; }}
        
        /* --- FIX: Ensure videos inside cards do not exceed screen width --- */
        .card video {{ width: 100%; height: auto; display: block; }}
        
        .caption-box {{ padding: 25px; background-color: #fff; border-top: 1px solid #eee; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; line-height: 1.6; white-space: pre-wrap; color: #333; }}
        .caption-line {{ display: block; }}
        
        .page-view {{ display: none; width: 100%; flex-direction: column; align-items: center; }}
        .page-view.active {{ display: flex; }}

        /* Collapsed Sidebar */
        body.sidebar-collapsed .dataset-nav {{ width: 50px; padding-left: 5px; padding-right: 5px; }}
        body.sidebar-collapsed .main-content {{ margin-left: 50px; width: calc(100% - 50px); }}
        body.sidebar-collapsed .dataset-btn, body.sidebar-collapsed .nav-subcategory {{ opacity: 0; pointer-events: none; white-space: nowrap; }}
        body.sidebar-collapsed #sidebar-toggle {{ background-color: #e6e6e6; }}
    </style>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const toggleBtn = document.getElementById('sidebar-toggle');
            const body = document.body;
            
            const overviewVideosMap = {overview_videos_map_json}; 
            const datasetToPageMap = {dataset_to_page_map_json}; 
            const pageToFirstDatasetMap = {page_to_first_dataset_map_json};
            const pagesData = {pages_data_json};

            const carouselIndices = {{}};

            toggleBtn.addEventListener('click', () => {{
                body.classList.toggle('sidebar-collapsed');
                toggleBtn.innerHTML = body.classList.contains('sidebar-collapsed') ? "&#9776;" : "&laquo;";
            }});

            let activePage = "Overview"; 
            let activeDatasetName = null; 
            const overviewContainer = document.getElementById('overview-container');
            const cardsContainer = document.getElementById('cards-container'); 
            const backBtn = document.getElementById('back-to-overview');

            let observer = new IntersectionObserver((entries, observer) => {{
                entries.forEach(entry => {{
                    let video = entry.target;
                    
                    if (entry.isIntersecting) {{
                        if (video.dataset.src) {{
                            video.src = video.dataset.src;
                            video.load();
                            video.removeAttribute('data-src');
                        }}
                        var playPromise = video.play();
                        if (playPromise !== undefined) {{
                            playPromise.catch(error => {{ }});
                        }}
                    }} else {{
                        video.pause();
                    }}
                }});
            }}, {{ rootMargin: "200px" }});

            function handleScrollSpy() {{
                if (activePage === "Overview") return;
                const blocks = cardsContainer.querySelectorAll('.content-block');
                
                blocks.forEach(block => {{
                    const rect = block.getBoundingClientRect();
                    if (rect.top >= -50 && rect.top < 300) {{
                        const id = block.id.replace('dataset-block-', '');
                        if (id !== activeDatasetName) {{
                            activeDatasetName = id;
                            updateSidebarHighlight();
                        }}
                    }}
                }});
            }}

            window.addEventListener('scroll', handleScrollSpy);

            function updateCarouselDots(datasetName, activeIndex) {{
                const dotsWrap = document.getElementById('carousel-dots-' + datasetName);
                if (!dotsWrap) return;

                const dots = dotsWrap.querySelectorAll('.carousel-dot');
                dots.forEach((dot, idx) => {{
                    dot.classList.toggle('active', idx === activeIndex);
                }});

                if (dots[activeIndex]) {{
                    dots[activeIndex].scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                }}
            }}

            window.setCarouselIndex = function(datasetName, newIndex) {{
                const videoList = overviewVideosMap[datasetName];
                if (!videoList || videoList.length === 0) return;

                if (carouselIndices[datasetName] === undefined) {{
                    carouselIndices[datasetName] = 0;
                }}

                if (newIndex >= videoList.length) newIndex = 0;
                if (newIndex < 0) newIndex = videoList.length - 1;

                carouselIndices[datasetName] = newIndex;

                const wrapper = document.getElementById('carousel-' + datasetName);
                const videoEl = wrapper.querySelector('video');
                const counterEl = wrapper.querySelector('.slide-counter');

                videoEl.src = videoList[newIndex];
                videoEl.play();

                if (counterEl) {{
                    counterEl.innerText = `${{newIndex + 1}} / ${{videoList.length}}`;
                }}

                updateCarouselDots(datasetName, newIndex);
            }};

            window.moveCarousel = function(datasetName, direction) {{
                const videoList = overviewVideosMap[datasetName];
                if (!videoList || videoList.length === 0) return;

                if (carouselIndices[datasetName] === undefined) {{
                    carouselIndices[datasetName] = 0;
                }}

                let newIndex = carouselIndices[datasetName] + direction;
                window.setCarouselIndex(datasetName, newIndex);
            }};

            // --- NAVIGATION HELPERS ---
            function setRoute(pageId, datasetName) {{
                activePage = pageId;
                activeDatasetName = datasetName;
                
                const hashValue = datasetName ? datasetName : pageId;
                if (window.location.hash !== '#' + encodeURIComponent(hashValue)) {{
                    window.history.pushState(null, null, '#' + encodeURIComponent(hashValue));
                }}
                
                updateView();
                
                if (datasetName) {{
                    setTimeout(() => {{
                        const targetCard = document.getElementById('dataset-block-' + datasetName);
                        if (targetCard) {{
                            targetCard.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        }}
                    }}, 10);
                }} else {{
                    window.scrollTo(0, 0);
                }}
            }}

            window.navigateToDataset = function(datasetName) {{
                const targetPage = datasetToPageMap[datasetName];
                if (!targetPage) return;
                setRoute(targetPage, datasetName);
            }};

            window.navigateToGroup = function(pageId) {{
                setRoute(pageId, null);
            }};

            window.backToOverview = function() {{
                const sectionDataset = activeDatasetName || pageToFirstDatasetMap[activePage] || null;
                activePage = "Overview";
                activeDatasetName = sectionDataset;

                if (window.location.hash !== '#Overview') {{
                    window.history.pushState(null, null, '#Overview');
                }}

                updateView();

                if (sectionDataset) {{
                    setTimeout(() => {{
                        const targetSection = document.getElementById('section-' + sectionDataset);
                        if (targetSection) {{
                            targetSection.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        }} else {{
                            window.scrollTo(0, 0);
                        }}
                    }}, 10);
                }} else {{
                    window.scrollTo(0, 0);
                }}
            }};

            function updateSidebarHighlight() {{
                const datasetBtns = document.querySelectorAll('.dataset-btn');
                datasetBtns.forEach(btn => {{
                    const targetPage = btn.dataset.target;
                    const targetDataset = btn.dataset.dataset; 

                    btn.classList.remove('active');

                    if (activePage === "Overview") {{
                         if (targetPage === "Overview") btn.classList.add('active');
                    }} 
                    else if (btn.classList.contains('level-2')) {{
                        if (targetPage === activePage) {{
                            btn.classList.add('active');
                        }}
                    }} 
                    else if (btn.classList.contains('level-3')) {{
                        if (targetDataset === activeDatasetName) {{
                            btn.classList.add('active');
                        }}
                    }}
                }});
            }}

            function renderPage(pageId) {{
                cardsContainer.innerHTML = ""; // Clear memory!
                
                const data = pagesData[pageId];
                if (!data) return;

                const headerDiv = document.createElement('div');
                headerDiv.className = "hierarchy-bar level-2-header";
                headerDiv.style.marginBottom = "40px";
                headerDiv.innerText = data.title;
                cardsContainer.appendChild(headerDiv);

                // --- Render Group Description (only if it exists) ---
                if (data.description) {{
                    const groupDescEl = document.createElement('div');
                    groupDescEl.className = "dataset-description";
                    groupDescEl.style.marginBottom = "30px";
                    groupDescEl.innerHTML = data.description;
                    cardsContainer.appendChild(groupDescEl);
                }}

                data.blocks.forEach(block => {{
                    const blockDiv = document.createElement('div');
                    blockDiv.className = "content-block";
                    blockDiv.id = "dataset-block-" + block.id;

                    if (data.is_group) {{
                         const titleEl = document.createElement('h3');
                         titleEl.className = "level-3-header";
                         titleEl.style.fontSize = "1.5rem";
                         titleEl.style.marginBottom = "20px";
                         titleEl.innerText = block.id;
                         blockDiv.appendChild(titleEl);
                    }}

                    if (block.description) {{
                        const descEl = document.createElement('div');
                        descEl.className = "dataset-description";
                        descEl.innerHTML = block.description;
                        blockDiv.appendChild(descEl);
                    }}

                    block.videos.forEach(vid => {{
                        const cardDiv = document.createElement('div');
                        cardDiv.className = "card";
                        
                        const videoTag = document.createElement('video');
                        videoTag.className = "lazy";
                        videoTag.setAttribute('data-src', vid.src);
                        videoTag.preload = "none";
                        videoTag.controls = true;
                        videoTag.autoplay = true;
                        videoTag.loop = true;
                        videoTag.muted = true;
                        videoTag.playsInline = true;
                        
                        cardDiv.appendChild(videoTag);

                        if (vid.caption) {{
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = vid.caption; 
                            while (tempDiv.firstChild) {{
                                cardDiv.appendChild(tempDiv.firstChild);
                            }}
                        }}

                        blockDiv.appendChild(cardDiv);
                    }});

                    cardsContainer.appendChild(blockDiv);
                }});

                const newVideos = cardsContainer.querySelectorAll('video.lazy');
                newVideos.forEach(v => observer.observe(v));
            }}

            function updateView() {{
                updateSidebarHighlight();

                if (activePage === "Overview") {{
                    cardsContainer.style.display = "none";
                    cardsContainer.innerHTML = ""; 
                    
                    overviewContainer.style.display = "block";
                    backBtn.style.display = "none"; 
                    
                    const overviewVideos = overviewContainer.querySelectorAll('video.lazy');
                    overviewVideos.forEach(v => observer.observe(v));

                }} else {{
                    overviewContainer.style.display = "none";
                    backBtn.style.display = "flex"; 
                    cardsContainer.style.display = "flex"; 

                    renderPage(activePage);
                }}
            }}

            // --- HANDLE INITIAL LOAD VIA URL ---
            function loadStateFromHash() {{
                const hash = window.location.hash.substring(1); 
                const decodedHash = decodeURIComponent(hash);
                
                if (!decodedHash || decodedHash === "Overview") {{
                    activePage = "Overview";
                    activeDatasetName = null;
                }} else {{
                    // Check if it matches a dataset first
                    if (datasetToPageMap[decodedHash]) {{
                        activePage = datasetToPageMap[decodedHash];
                        activeDatasetName = decodedHash;
                    }} else if (pagesData[decodedHash]) {{
                        // Or just a page group
                        activePage = decodedHash;
                        activeDatasetName = null;
                    }} else {{
                        // Fallback
                        activePage = "Overview";
                    }}
                }}
                
                updateView();

                // Scroll to target if specific dataset
                if (activeDatasetName && activePage !== "Overview") {{
                    setTimeout(() => {{
                        const targetCard = document.getElementById('dataset-block-' + activeDatasetName);
                        if (targetCard) {{
                            targetCard.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        }}
                    }}, 100);
                }}
            }}

            window.addEventListener('hashchange', loadStateFromHash);

            document.querySelectorAll('.dataset-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    if (window.innerWidth < 768) {{
                        body.classList.add('sidebar-collapsed');
                        toggleBtn.innerHTML = "&#9776;";
                    }}
                }});
            }});

            loadStateFromHash();
        }});
    </script>
</head>
<body>

    <button id="sidebar-toggle" title="Toggle Sidebar">&laquo;</button>

    <div class="dataset-nav">
        <button class="dataset-btn overview-btn" data-target="Overview" onclick="backToOverview()">Overview</button>
        {dataset_nav_buttons}
    </div>

    <div class="main-content">
        <header class="paper-header">
            <h1 class="paper-title">{paper_title}</h1>
            
            <div class="paper-meta">
                <div class="paper-authors">{authors_html}</div>
                <div class="paper-institutions">{institutions_html}</div>
                <div class="link-buttons">{link_buttons_html}</div>
            </div>
        </header>

        <button id="back-to-overview" class="back-btn" onclick="backToOverview()">
            <span>&larr;</span> Back to Overview
        </button>

        <div id="overview-container" class="overview-container">
            <div class="abstract-section">
                <div class="abstract-title">Abstract</div>
                <div class="abstract-content">
                    {abstract_text}
                </div>
            </div>
            {overview_html}
        </div>

        <div id="cards-container" class="container"></div>

        <div class="paper-footer">
        </div>
    </div>
    
    <div id="clustrmaps-widget-container">
        <script></script>
    </div>

</body>
</html>
"""

def sort_key(filepath):
    basename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(basename)[0]
    
    if name_without_ext.isdigit():
        return (0, int(name_without_ext))
    return (1, name_without_ext)


def generate_single_index(input_folder):
    if not os.path.exists(input_folder):
        print(f"Error: Input directory '{input_folder}' not found.")
        return

    # 1. Scan available datasets
    found_datasets = set([d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))])
    
    if not found_datasets:
        print(f"No datasets found inside {input_folder}")
        return

    # --- PROCESS AUTHORS & INSTITUTIONS ---
    authors_html = ""
    for i, (name, indices) in enumerate(AUTHORS):
        sup_str = ",".join([str(idx + 1) for idx in indices])
        authors_html += f'<span class="author-span">{name}<sup>{sup_str}</sup></span>'
        if i < len(AUTHORS) - 1:
            authors_html += ", "
    
    authors_string = " and ".join([a[0] for a in AUTHORS])

    institutions_html = ""
    for i, inst in enumerate(INSTITUTIONS):
        institutions_html += f'<span class="institution-span"><sup>{i+1}</sup>{inst}</span>'
        if i < len(INSTITUTIONS) - 1:
            institutions_html += ", "

    # --- PROCESS LINKS ---
    link_buttons_html = ""
    if ARXIV_LINK:
        paper_icon = '<svg class="link-icon" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>'
        link_buttons_html += f'<a href="{ARXIV_LINK}" target="_blank" class="link-btn">{paper_icon} arXiv</a>'
    
    if CODE_LINK:
        code_icon = '<svg class="link-icon" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>'
        link_buttons_html += f'<a href="{CODE_LINK}" target="_blank" class="link-btn">{code_icon} GitHub</a>'

    # --- FLATTEN CONFIG FOR PAGES ---
    pages = []
    used_datasets = set()
    dataset_to_page_map = {} 
    page_to_first_dataset_map = {}
    
    overview_structure = [] 

    dataset_nav_html = ""

    # A. Process Configured Categories
    for category_name, items in SIDEBAR_CONFIG:
        dataset_nav_html += f'<div class="nav-category">{category_name}</div>\n'
        
        cat_subitems = [] 

        for item in items:
            is_group = False
            sub_name = ""
            sub_datasets = []

            if isinstance(item, tuple):
                if len(item) == 2 and isinstance(item[1], list):
                    is_group = True
                    sub_name, sub_datasets = item
                elif len(item) == 1:
                    is_group = False
                    sub_name = item[0]
                    sub_datasets = [sub_name]
            elif isinstance(item, str):
                is_group = False
                sub_name = item
                sub_datasets = [sub_name]

            valid_subs = [d for d in sub_datasets if d in found_datasets]
            
            if valid_subs:
                if is_group:
                    dataset_nav_html += f'<button class="dataset-btn level-2" data-target="{sub_name}" onclick="navigateToGroup(\'{sub_name}\')">{sub_name}</button>\n'
                    pages.append({
                        "id": sub_name,
                        "title": sub_name,
                        "datasets": valid_subs,
                        "is_group": True
                    })
                    page_to_first_dataset_map[sub_name] = valid_subs[0]

                    for d_name in valid_subs:
                        dataset_nav_html += f'<button class="dataset-btn level-3" data-target="{sub_name}" data-dataset="{d_name}" onclick="navigateToDataset(\'{d_name}\')">{d_name}</button>\n'
                        used_datasets.add(d_name)
                        dataset_to_page_map[d_name] = sub_name
                        dataset_to_page_map[sub_name] = sub_name
                else:
                    d_name = valid_subs[0]
                    dataset_nav_html += f'<button class="dataset-btn level-2" data-target="{d_name}" onclick="navigateToGroup(\'{d_name}\')">{d_name}</button>\n'
                    pages.append({
                        "id": d_name,
                        "title": d_name,
                        "datasets": [d_name],
                        "is_group": False
                    })
                    page_to_first_dataset_map[d_name] = d_name
                    
                    used_datasets.add(d_name)
                    dataset_to_page_map[d_name] = d_name

                cat_subitems.append((sub_name, valid_subs, is_group))

        if cat_subitems:
            overview_structure.append((category_name, cat_subitems))

    # B. Process "Others"
    remaining_datasets = sorted(list(found_datasets - used_datasets))
    if remaining_datasets:
        dataset_nav_html += '<div class="nav-category">Others</div>\n'
        others_subitems = []
        for d_name in remaining_datasets:
            pages.append({
                "id": d_name,
                "title": d_name,
                "datasets": [d_name],
                "is_group": False
            })
            dataset_nav_html += f'<button class="dataset-btn level-2" data-target="{d_name}" onclick="navigateToGroup(\'{d_name}\')">{d_name}</button>\n'
            dataset_to_page_map[d_name] = d_name
            page_to_first_dataset_map[d_name] = d_name
            others_subitems.append((d_name, [d_name], False))
        
        overview_structure.append(("Others", others_subitems))

    # --- GENERATE OVERVIEW HTML ---
    overview_videos_map = {} 
    
    overview_html = ""
    for category_name, sub_items in overview_structure:
        overview_html += f'''
        <div class="hierarchy-bar level-1-header">
            {category_name}
        </div>
        '''
        
        for sub_name, d_list, is_group in sub_items:
            overview_html += f'''
            <div class="hierarchy-bar level-2-header">
                {sub_name}
            </div>
            '''
            
            # Only render group description in overview if it IS a group
            if is_group:
                group_desc = DATASET_DESCRIPTIONS.get(sub_name, "")
                if group_desc:
                    overview_html += f'<div class="dataset-description" style="margin-bottom: 30px; text-align: left;">{group_desc}</div>'

            for d_name in d_list:
                d_path = os.path.join(input_folder, d_name)
                files = sorted(glob.glob(os.path.join(d_path, "*.mp4")), key=sort_key)
                rel_files = [os.path.join(input_folder, d_name, os.path.basename(f)) for f in files]
                overview_videos_map[d_name] = rel_files
                
                if not rel_files: continue
                
                first_video = rel_files[0]
                total_count = len(rel_files)
                desc = DATASET_DESCRIPTIONS.get(d_name, "")
                
                header_html = ""
                if is_group:
                    header_html = f'''
                    <div class="overview-section-header">
                        <h4 class="level-3-header">{d_name}</h4>
                    </div>
                    '''

                dots_html = "".join(
                    [
                        f"<button class=\"carousel-dot{' active' if i == 0 else ''}\" onclick=\"setCarouselIndex('{d_name}', {i})\" aria-label=\"Slide {i + 1}\"></button>"
                        for i in range(total_count)
                    ]
                )
                
                section_html = f"""
                <div class="overview-section" id="section-{d_name}">
                    {header_html}
                    <div class="overview-desc">{desc}</div>
                    
                    <div class="carousel-wrapper" id="carousel-{d_name}">
                        <button class="carousel-btn left" onclick="moveCarousel('{d_name}', -1)">&#10094;</button>
                        <video class="lazy" data-src="{first_video}" preload="none" muted autoplay loop playsinline></video>
                        <button class="carousel-btn right" onclick="moveCarousel('{d_name}', 1)">&#10095;</button>
                        <div class="slide-counter">1 / {total_count}</div>
                    </div>

                    <div class="carousel-dots" id="carousel-dots-{d_name}">
                        {dots_html}
                    </div>
                    
                    <div class="overview-action">
                        <button class="btn-view-all" onclick="navigateToDataset('{d_name}')">View Full Examples &rarr;</button>
                    </div>
                </div>
                """
                overview_html += section_html

    # --- GATHER CONTENT DATA ---
    pages_data = {}
    
    for page in pages:
        page_id = page["id"]
        
        # --- FIXED: Only set group description if it IS a group ---
        if page["is_group"]:
            group_description = DATASET_DESCRIPTIONS.get(page_id, "")
        else:
            group_description = ""
        
        current_page_data = {
            "title": page["title"],
            "description": group_description,
            "is_group": page["is_group"],
            "blocks": []
        }
        
        for d_name in page["datasets"]:
            dataset_path = os.path.join(input_folder, d_name)
            mp4_files = sorted(glob.glob(os.path.join(dataset_path, "*.mp4")), key=sort_key)
            desc = DATASET_DESCRIPTIONS.get(d_name, "")

            block_data = {
                "id": d_name,
                "description": desc,
                "videos": []
            }
            
            for mp4_path in mp4_files:
                filename = os.path.basename(mp4_path)
                relative_video_path = os.path.join(input_folder, d_name, filename)
                
                json_filename = filename.replace(".mp4", ".json")
                json_path = os.path.join(dataset_path, json_filename)
                
                caption_html_str = ""
                if os.path.exists(json_path):
                    caption_html_str += '<div class="caption-box">'
                    try:
                        with open(json_path, 'r') as jf:
                            data = json.load(jf)
                            if isinstance(data, list):
                                for line in data:
                                    text = line.get('text', '')
                                    color = line.get('color', [0, 0, 0]) 
                                    hex_color = "#{:02x}{:02x}{:02x}".format(*color)
                                    caption_html_str += f'<span class="caption-line" style="color: {hex_color};">{text}</span>'
                    except Exception:
                        pass
                    caption_html_str += '</div>'
                
                block_data["videos"].append({
                    "src": relative_video_path,
                    "caption": caption_html_str
                })
            
            current_page_data["blocks"].append(block_data)
        
        pages_data[page_id] = current_page_data

    # --- FINALIZE ---
    dataset_descriptions_json = json.dumps(DATASET_DESCRIPTIONS)
    overview_videos_map_json = json.dumps(overview_videos_map)
    dataset_to_page_map_json = json.dumps(dataset_to_page_map)
    page_to_first_dataset_map_json = json.dumps(page_to_first_dataset_map)
    pages_data_json = json.dumps(pages_data)

    final_html = HTML_TEMPLATE.format(
        paper_title=PAPER_TITLE,
        authors_html=authors_html,
        institutions_html=institutions_html,
        authors_string=authors_string,
        abstract_text=ABSTRACT_TEXT,
        link_buttons_html=link_buttons_html,
        dataset_nav_buttons=dataset_nav_html,
        overview_html=overview_html,
        dataset_descriptions_json=dataset_descriptions_json,
        overview_videos_map_json=overview_videos_map_json,
        dataset_to_page_map_json=dataset_to_page_map_json,
        page_to_first_dataset_map_json=page_to_first_dataset_map_json,
        pages_data_json=pages_data_json,
        dataset_category_map_json="{}" 
    )

    output_path = "./index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"\nSuccessfully generated dashboard at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile all datasets into a single HTML dashboard.")
    parser.add_argument("--input_folder", type=str, default="./video", help="Path to the folder containing dataset subdirectories.")
    
    args = parser.parse_args()
    
    generate_single_index(args.input_folder)