"""
How to run:
    python compile_html_final.py

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

if False:
    AUTHORS = [
        ("Koichi Namekata", [0], "https://kmcode1.github.io/"),
        ("Andrea Vedaldi", [0], "https://www.robots.ox.ac.uk/~vedaldi/"),
    ]

    INSTITUTIONS = [
        "University of Oxford",
    ]
else:
    AUTHORS = [
        ("Anonymous Authors", [0], "https://gear-vdm.github.io/"),
    ]

    INSTITUTIONS = [
        "Anonymous Institutions", 
    ]


ARXIV_LINK = "https://gear-vdm.github.io/"
CODE_LINK = "https://gear-vdm.github.io/"


ABSTRACT_TEXT = """
<p>
Video diffusion models are increasingly viewed as a promising route toward emulating the physical world. However, their ability to reason about mechanical systems—characterized by strict topological and kinematic constraints—remains significantly underexplored. In this work, we investigate whether video diffusion transformers (DiTs) can effectively simulate and design mechanical systems, using 2D involute gear trains as a testbed. Gear mechanisms represent a simple yet challenging
domain: determining the motion of such systems requires capturing long cause-effect interactions, where a single driving gear dictates the rotational parity of the entire mechanism.
</p>
<p>
We first demonstrate that off-the-shelf video generative models fail to produce physically plausible gear interactions. 
To diagnose this, we formally define the <i>simulation</i> and <i>design</i> of gear systems as video generation tasks, supported by the rigorous evaluation strategy. 
We then fine-tune DiTs in both non-autoregressive and autoregressive paradigms.
</p>
<p>
Our experiments reveal that even lightly fine-tuned DiTs demonstrate strong kinematic reasoning in simulation tasks, where non-autoregressive models, in particular, internally resembles graph-traversal reasonings. 
However, we also warn that these models are brittle: performance degrades significantly when structural complexity (gear count) exceeds the training distribution.
</p>
<p>
For the design task, we find that naively fine-tuned DiTs struggle to produce valid spatial layouts, often generating gears detached from others.
To understand the reasons, we demonstrate that the topology of a gear system is determined during the extremely high-noise regime of the flow path—a phase often overlooked by standard training noise-schedules.
By introducing a simple modification to focus training on such high-noise regime, we significantly improve the model’s ability to generate valid topology.
</p>
<p>
Ultimately, our results suggest that while video DiTs possess a high potential for synthesizing mechanical systems, they require dedicated investigation for its training strategies. This work provides a crucial insights toward achieving physically faithful video models.
</p>
"""


# --- 3-LEVEL HIERARCHY CONFIG ---
# The script automatically detects if an item is a "Group" (tuple with list) or "Single" (string)
SIDEBAR_CONFIG = [
    ("Motivation", [
        "Animating Gear Systems with Commercial Video Models",
    ]),
    ("Study 1: Simulating Gear Systems (Sec 4)", [
        "Non-autoregressive Simulation",
        "Autoregressive Simulation",
        ("Non-autoregressive vs Autoregressive Simulation", [
            "Quantitative Comparisons",
            "Per-sample Kinematic Alignment Error",
            "Failure Cases of Non-autoregressive Simulation",
            "Failure Cases of Autoregressive Simulation",
            "Generalization to Unseen Complexity",
        ]),
        "PCA Analysis",
    ]),
    ("Study 2: Designing Gear Systems (Sec 5)", [
        "Non-autoregressive Design",
        "Autoregressive Design",
        ("Ablation: Default training noise schedule", [
            "Ablation: Non-autoregressive Design",
            "Ablation: Autoregressive Design",
            "Quantitative Analysis"
        ]),
        "Non-autoregressive vs Autoregressive Design",
    ]),
    ("Conclusions: ", []),
]


DATASET_DESCRIPTIONS = {
    # --- DATASETS (Bottom Level) ---
    "Animating Gear Systems with Commercial Video Models": """
    <div>
    <p>
        In this work, we explore the capabilities of state-of-the-art video generative models built on Diffusion Transformers (DiTs) to simulate and design mechanical systems, using 2D gear systems as a testbed. 
        To start with, we first examine off-the-shelf commercial video generative models<sup>*</sup> on their ability to generate plausible gear interactions via first-frame conditioned video generation (I2V) tasks. 
        As shown below, while these models demonstrate remarkable visual fidelity, they struggle to adhere to basic kinematic constraints, resulting in meshed gears with conflicting rotational directions and mismatched angular velocities.
    </p>
    
    <p style="margin-top: 1em;">
        <small><sup>*</sup>Videos were generated using <a href="https://lumalabs.ai" target="_blank" rel="noopener noreferrer">lumalabs.ai</a>.</small>
    </p>
    </div>
    """,
    "Study 1: Simulating Gear Systems (Sec 4)": """
    <div>
    <p>
        In the simulation task, the model takes the <b>spatial layout of a gear system</b> at the first frame and a conditioning video of <b>a single driving gear</b> as inputs. 
        The objective is to simulate the motion of the remaining gears while adhering to the kinematic constraints of meshing pairs. 
        We study both non-autoregressive and autoregressive formulations to assess the VDM's ability to reason about individual gear motion across long chains of gear interactions.
    </p>
    </div>
    """,
    "Non-autoregressive Simulation": """
    The non-autoregressive formulation animates the entire gear mechanism simultaneously in a single generation process. 
    This setting evaluates whether a single generation process is sufficient for the VDM to reason about kinematic dependencies across the long-range interacting gear chains.
    """,
    "Autoregressive Simulation": """
    The autoregressive formulation animates the system through an iterative generative process. 
    In each generation process, the model only animates gears adjacent to those whose motion has already been determined.
    """,
    "Study 2: Designing Gear Systems (Sec 5)": """
    <div>
    <p>
        In the design task, the model is conditioned solely on a video of a single driving gear and must synthesize a functional multi-gear system. 
        We evaluate whether the VDM can learn to generate gear systems that form a valid tree topology while satisfying kinematic constraints. 
        Similar to Study 1, we compare the performance of non-autoregressive and autoregressive formulations.
    </p>
    </div>
    """,
    "Non-autoregressive Design": """
    The non-autoregressive design synthesizes the entire multi-gear system simultaneously in a single generation process.
    """,
    "Autoregressive Design": """
    The autoregressive design progressively constructs the mechanism, adding a new gear that meshes with the existing system at each step.
    """,
    "Quantitative Comparisons": """
    <div>
    <p>
        The table below summarizes simulation accuracy for non-autoregressive and autoregressive formulations. 
        Overall, both achieve similar performance across metrics.
    </p>
    <div class="table-wrap">
        <table class="latex-table">
            <thead>
                <tr>
                    <th></th>
                    <th></th>
                    <th colspan="2" class="center cmid">Physical Correctness</th>
                    <th colspan="3" class="center cmid">Fidelity to GT</th>
                </tr>
                <tr class="headrule">
                    <th># of Gears</th>
                    <th>Formulation</th>
                    <th>E<sub>topo</sub> &darr;</th>
                    <th>E<sub>kine</sub> &darr;</th>
                    <th>E<sup>GT</sup><sub>topo</sub> &darr;</th>
                    <th>E<sup>GT</sup><sub>kine</sub> &darr;</th>
                    <th>E<sup>GT</sup><sub>spat</sub> &darr;</th>
                </tr>
            </thead>
            <tbody>
                <tr class="midrule">
                    <td rowspan="2">5</td>
                    <td>Non-autoregressive</td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.0085"><span class="u">0.0085</span></td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.0497"><span class="u">0.0497</span></td>
                    <td data-value="0.0475">0.0475</td>
                </tr>
                <tr>
                    <td>Autoregressive</td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.0115">0.0115</td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.0660">0.0660</td>
                    <td data-value="0.0402"><span class="u">0.0402</span></td>
                </tr>
                <tr class="midrule">
                    <td rowspan="2">10</td>
                    <td>Non-autoregressive</td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.0223"><span class="u">0.0223</span></td>
                    <td data-value="0.0"><span class="u">0.0000</span></td>
                    <td data-value="0.1349">0.1349</td>
                    <td data-value="0.0539">0.0539</td>
                </tr>
                <tr>
                    <td>Autoregressive</td>
                    <td data-value="0.001">0.001</td>
                    <td data-value="0.0285">0.0285</td>
                    <td data-value="0.001">0.001</td>
                    <td data-value="0.1307"><span class="u">0.1307</span></td>
                    <td data-value="0.0401"><span class="u">0.0401</span></td>
                </tr>
                <tr class="midrule">
                    <td rowspan="2">15</td>
                    <td>Non-autoregressive</td>
                    <td data-value="0.0007">0.0007</td>
                    <td data-value="0.0224"><span class="u">0.0224</span></td>
                    <td data-value="0.0013">0.0013</td>
                    <td data-value="0.1046"><span class="u">0.1046</span></td>
                    <td data-value="0.0441"><span class="u">0.0441</span></td>
                </tr>
                <tr>
                    <td>Autoregressive</td>
                    <td data-value="0.0000"><span class="u">0.0000</span></td>
                    <td data-value="0.0352">0.0352</td>
                    <td data-value="0.0000"><span class="u">0.0000</span></td>
                    <td data-value="0.1357">0.1357</td>
                    <td data-value="0.0732">0.0732</td>
                </tr>
                <tr class="midrule">
                    <td rowspan="2">20</td>
                    <td>Non-autoregressive</td>
                    <td data-value="0.0005">0.0005</td>
                    <td data-value="0.0427">0.0427</td>
                    <td data-value="0.0005">0.0005</td>
                    <td data-value="0.1829"><span class="u">0.1829</span></td>
                    <td data-value="0.0670"><span class="u">0.0670</span></td>
                </tr>
                <tr>
                    <td>Autoregressive</td>
                    <td data-value="0.0000"><span class="u">0.0000</span></td>
                    <td data-value="0.0396"><span class="u">0.0396</span></td>
                    <td data-value="0.0005"><span class="u">0.0005</span></td>
                    <td data-value="0.1945">0.1945</td>
                    <td data-value="0.0679">0.0679</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="table-note">
        Performance Comparison of Non-Autoregressive and Autoregressive Formulations trained and inference on the specific number of gears. Lower values indicate better performance.
    </div>
    </div>
    """,
    "Per-sample Kinematic Alignment Error": """
    <div>
    <p>
        We plot the per-sample kinematic alignment error (E<sup>GT</sup><sub>kine</sub>) for a 20-gear system, comparing non-autoregressive and autoregressive simulations.
        Each point corresponds to one sample (x-axis is the sample index); lower values indicate closer agreement with the ground-truth kinematics.
    </p>
    <div style="width: 100%; text-align: center;">
        <img src="per_sample_kinematic_tracking_error.png" alt="Per-sample kinematic alignment error for a 20-gear system." style="max-width: 100%; height: auto;">
    </div>
    <p>
        While most samples maintain low error rates, both formulations occasionally exhibit catastrophic failures that result in sharp error spikes. 
        As visualized below, their failure modes differ: the non-autoregressive formulation flips rotational parity at a subgraph level, whereas the autoregressive formulation accumulates mistakes following an early incorrect prediction. 
        Furthremore, autoregressive simulation generally exhibits a slightly higher overall error due to its tendency to compound deviations over iterative generation processes.
    </p>
    </div>
    """,
    "Failure Cases of Non-autoregressive Simulation": """
    <div>
    <p>
    In non-autoregressive simulation, failures often occur at the subgraph level: a cluster of connected gears is assigned the wrong rotational parity, leading to spikes in kinematic error.
    </p>
    <p style="margin-top: 1em;">
        <small> Note:In the visualization below, green circles denote correct gear movements relative to the ground truth, whereas blue circles denote incorrect motion. </small>
    </p>
    </div>
    """,
    "Failure Cases of Autoregressive Simulation": """
    <div>
    <p>
    The autoregressive simulation suffers from error accumulation. Once a specific gear is assigned an incorrect movements, later steps inherit and amplify the error.
    </p>
    <p style="margin-top: 1em;">
        <small> Note: In the visualization below, green circles denote correct gear movements relative to the ground truth, whereas blue circles denote incorrect motion. </small>
    </p>
    </div>
    """,
    "Generalization to Unseen Complexity": """
    <div>
    <p>
        We evaluate zero-shot generalization to unseen gear counts by training and testing on differing numbers of gears. 
        When the complexity at inference exceeds that of the training set, performance degrades unpredictably for both non-autoregressive and autoregressive simulations. 
        This drop suggests that the model does not necessarily learn fully generalizable reasoning capabilities, highlighting the necessity of aligning the training data distribution with expected inference complexity to guarantee robust performance.
    </p>
    <div class="table-wrap">
        <table class="latex-table heatmap-generalization">
            <thead>
                <tr>
                    <th></th>
                    <th>Metric:</th>
                    <th colspan="4" class="center cmid">Non-autoregressive</th>
                    <th colspan="4" class="center cmid sep-left">Autoregressive</th>
                </tr>
                <tr>
                    <th></th>
                    <th>E<sup>GT</sup><sub>kine</sub> &darr;</th>
                    <th colspan="4" class="center">Inference</th>
                    <th colspan="4" class="center sep-left">Inference</th>
                </tr>
                <tr class="headrule">
                    <th></th>
                    <th></th>
                    <th>5 Gears</th>
                    <th>10 Gears</th>
                    <th>15 Gears</th>
                    <th>20 Gears</th>
                    <th class="sep-left">5 Gears</th>
                    <th>10 Gears</th>
                    <th>15 Gears</th>
                    <th>20 Gears</th>
                </tr>
            </thead>
            <tbody>
                <tr class="midrule">
                    <th rowspan="4" class="vlabel">Train</th>
                    <th scope="row">5 Gears</th>
                    <td data-group="nar" data-value="0.0496">0.0496</td>
                    <td data-group="nar" data-value="0.2481">0.2481</td>
                    <td data-group="nar" data-value="0.4025">0.4025</td>
                    <td data-group="nar" data-value="0.7964">0.7964</td>
                    <td class="sep-left" data-group="ar" data-value="0.0661">0.0661</td>
                    <td data-group="ar" data-value="0.0584">0.0584</td>
                    <td data-group="ar" data-value="0.1360">0.1360</td>
                    <td data-group="ar" data-value="0.2383">0.2383</td>
                </tr>
                <tr>
                    <th scope="row">10 Gears</th>
                    <td data-group="nar" data-value="0.0534">0.0534</td>
                    <td data-group="nar" data-value="0.1349">0.1349</td>
                    <td data-group="nar" data-value="0.2103">0.2103</td>
                    <td data-group="nar" data-value="0.3461">0.3461</td>
                    <td class="sep-left" data-group="ar" data-value="0.0758">0.0758</td>
                    <td data-group="ar" data-value="0.1101">0.1101</td>
                    <td data-group="ar" data-value="0.2137">0.2137</td>
                    <td data-group="ar" data-value="0.2950">0.2950</td>
                </tr>
                <tr>
                    <th scope="row">15 Gears</th>
                    <td data-group="nar" data-value="0.0459">0.0459</td>
                    <td data-group="nar" data-value="0.0562">0.0562</td>
                    <td data-group="nar" data-value="0.1046">0.1046</td>
                    <td data-group="nar" data-value="0.1676">0.1676</td>
                    <td class="sep-left" data-group="ar" data-value="0.0983">0.0983</td>
                    <td data-group="ar" data-value="0.1108">0.1108</td>
                    <td data-group="ar" data-value="0.1360">0.1360</td>
                    <td data-group="ar" data-value="0.3076">0.3076</td>
                </tr>
                <tr>
                    <th scope="row">20 Gears</th>
                    <td data-group="nar" data-value="0.0512">0.0512</td>
                    <td data-group="nar" data-value="0.0607">0.0607</td>
                    <td data-group="nar" data-value="0.1853">0.1853</td>
                    <td data-group="nar" data-value="0.1829">0.1829</td>
                    <td class="sep-left" data-group="ar" data-value="0.0916">0.0916</td>
                    <td data-group="ar" data-value="0.0758">0.0758</td>
                    <td data-group="ar" data-value="0.1185">0.1185</td>
                    <td data-group="ar" data-value="0.1945">0.1945</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="table-note">
        Zero-shot generalization across mechanism complexity. We report E<sup>GT</sup><sub>kine</sub> for models trained on a maximum gear count and evaluated at different inference counts.
    </div>
    </div>
    """,

    
    "PCA Analysis": """
    <div>
    <p>
        While we have observed that video diffusion transformers (DiTs) can simulate gear systems with high success rates after minimal fine-tuning, 
        an important question arises: how do these models reason about complex kinematic dependencies? 
        To investigate this, we PCA-visualize the self-attention maps of video diffusion transformers fine-tuned for non-autoregressive simulation task, trained on 20 gear systems.
    </p>
    <div style="width: 100%; text-align: center;">
        <img src="PCA.png" alt="PCA visualization of feature maps." style="max-width: 100%; height: auto;">
    </div>
    <p>
        As visualized above, layer 6 − 21 reveal a form of recursive propagation of signals originating from the driving
        gear and spreading to its neighbors. 
        In layer 25, the internal feature maps distinguish gears by its rotational parity.
        This empirical evidence suggests that the transformer layers may be executing a learned, recursive graph algorithm to 
        determine the kinematic state of each component. 
        While we do not claim that diffusion transformers always converge to such algorithmic solutions, these observations 
        highlight their ability to learn algorithmic reasoning from video data without explicitly being taught to perform such reasoning steps.
    </p>
    </div>
    """,
    "Ablation: Default training noise schedule": """
    <div>
        <p>
        In this design task, we have observed that naively fine-tuned DiTs struggle to produce valid topological layouts, often generating gears detached from others.
        The key reasons behind this is that the generation of layout is determined during the extremely high-noise regime (>= 0.98) of the flow path, a phase often overlooked by standard training noise-schedules.
        </p>
        <div style="width: 100%; text-align: center;">
            <img src="noise_schedule.png" alt="Noise schedule" style="max-width: 100%; height: auto;">
            <div class="table-note"><b>The role of noise levels across the generation process in autoregressive design task.</b> <i>Graph:</i> Visualization of how the contribution of each potential gear configuration (each configuration is represented as a line) changes across different noise levels &sigma; within a single generation process. <i>Overlayed image:</i> Gear configurations whose contributions converges to 0 at each noise-level &sigma;. Our analysis reveals that the model already "locks in" specific spatial layouts at &sigma; = 0.98, with only minor refinements occurring afterwards.</div>
        </div>
        <div style="width: 100%; text-align: center; margin-top: 1.5em;">
            <video src="one_step_pred.mp4" autoplay loop muted playsinline controls style="max-width: 100%; height: auto;"></video>
            <div class="table-note"><sup>*</sup> <b>One-step predictions during the simulated denoising process in autoregressive design task.</b> Visualizations of the one-step prediction across the analytically constructed flow path. By &sigma; = 0.98, the model has already committed to a specific spatial layout.</div>
        </div>
        As will be shown below, by simply adjusting the training noise schedule to focus on those extremely high-noise regimes, we observe drastic improvements in the model's ability to generate valid topologies.    
    </div>
    """,
    "Ablation: Non-autoregressive Design":"""
    When the model is trained with the default noise schedule, the model struggles to learn to generate the correct topological layout.
    """,
    "Ablation: Autoregressive Design": """
    Surprisingly, even in the autoregressive setting, where the task is simplified to generating only a single gear at a time condition on the existing layout, the model trained on the the default noise schedule still struggles to generate gears that are properly attached to the existing system. 
    """,
    "Quantitative Analysis": """
    <div>
    <p>
        Consistent with the visual results shown above, we quantitatively demonstrate that our schedule achieves a substantial reduction in topological error for both non-autoregressive and autoregressive settings.
    </p>
    <div class="table-wrap">
        <table class="latex-table">
            <thead>
                <tr>
                    <th rowspan="2">Schedule</th>
                    <th colspan="2" class="center cmid">Non-autoregressive (NAR)</th>
                    <th colspan="2" class="center cmid">Autoregressive (AR)</th>
                </tr>
                <tr class="headrule">
                    <th>E<sub>topo</sub> &darr;</th>
                    <th>E<sub>kine</sub> &darr;</th>
                    <th>E<sub>topo</sub> &darr;</th>
                    <th>E<sub>kine</sub> &darr;</th>
                </tr>
            </thead>
            <tbody>
                <tr class="midrule">
                    <th scope="row">Original Schedule</th>
                    <td data-value="0.1306">0.1306</td>
                    <td data-value="0.1877">0.1877</td>
                    <td data-value="0.1385">0.1385</td>
                    <td data-value="0.1695">0.1695</td>
                </tr>
                <tr class="midrule">
                    <th scope="row">Our Schedule</th>
                    <td data-value="0.0794"><b>0.0794</b></td>
                    <td data-value="0.1808"><b>0.1808</b></td>
                    <td data-value="0.0736"><b>0.0736</b></td>
                    <td data-value="0.1139"><b>0.1139</b></td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="table-note">
        We compare topological and kinematic errors with and without our schedule. All models are trained to generate up to 20 gears. Lower values indicate better performance.
    </div>
    </div>
    """,
    "Non-autoregressive vs Autoregressive Design": """
    <div>
    <p>
        Finally, we evaluate the performance gap between non-autoregressive and autoregressive models. 
        The qualitative examples below and quantitative results in the table above demonstrate that autoregressive models demonstrate a much higher frequency of generating valid topologies and kinematic relationships. 
        This advantage likely stems from the sequential nature of the autoregressive approach, which breaks down complex system generation into manageable, step-by-step gear synthesis for the DiT backbone.
    </p>
    </div>
    """
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
        .paper-authors .author-link {{
            color: inherit;
            text-decoration-line: underline;
            text-decoration-style: solid;
            text-decoration-color: rgba(0, 120, 212, 0.35);
            text-decoration-thickness: 2px;
            text-underline-offset: 3px;
            cursor: pointer;
            transition: color 0.2s ease, text-decoration-color 0.2s ease;
        }}
        .paper-authors .author-link:hover {{
            color: var(--primary-color);
            text-decoration-color: var(--primary-color);
        }}
        .paper-authors .author-link:focus-visible {{
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
            text-decoration-color: transparent;
        }}
        .paper-institutions {{ font-size: 1rem; color: #666; margin-bottom: 10px; font-weight: 400; }}
        .paper-venue {{ font-size: 1.15rem; color: #444; margin-bottom: 18px; font-weight: 600; letter-spacing: 0.4px; }}
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
        .table-wrap {{ overflow-x: auto; }}
        .table-note {{ font-size: 12px; color: #666; margin-top: 6px; }}
        .latex-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            border-top: 1px solid #d6d6d6;
            border-bottom: 1px solid #d6d6d6;
            background: #ffffff;
        }}
        .latex-table th, .latex-table td {{
            padding: 8px 12px;
            vertical-align: middle;
            border-right: 1px solid #e2e2e2;
        }}
        .latex-table th {{
            font-weight: 600;
            color: #222;
            background: #f5f5f5;
        }}
        .latex-table td {{ color: #333; }}
        .latex-table td[data-value] {{ text-align: right; font-variant-numeric: tabular-nums; }}
        .latex-table.heatmap td[data-value] {{ transition: background-color 0.2s ease; }}
        .latex-table tr td:last-child, .latex-table tr th:last-child {{ border-right: none; }}
        .latex-table .center {{ text-align: center; }}
        .latex-table .cmid {{ border-bottom: 1px solid #d6d6d6; }}
        .latex-table .headrule th {{ border-bottom: 1px solid #d6d6d6; }}
        .latex-table .midrule td, .latex-table .midrule th {{ border-top: 1px solid #d6d6d6; }}
        .latex-table .doublemid td, .latex-table .doublemid th {{ border-top: 1px solid #d6d6d6; }}
        .latex-table .sep-left {{ border-left: 1px solid #d6d6d6; }}
        .latex-table tbody tr:nth-child(odd) td {{ background: #ffffff; }}
        .latex-table tbody tr:hover td {{ background: #f7f7f7; }}
        .latex-table .u {{
            text-decoration: underline;
            text-decoration-thickness: 2px;
            text-underline-offset: 2px;
            text-decoration-color: #444;
        }}
        .latex-table .vlabel {{
            writing-mode: vertical-rl;
            transform: rotate(180deg);
            text-align: center;
            letter-spacing: 0.5px;
            color: #222;
        }}

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

            function applyHeatmap() {{
                const tables = document.querySelectorAll('table.heatmap-generalization');
                tables.forEach(table => {{
                    const applyGroup = (groupName, exponent) => {{
                        const cells = Array.from(
                            table.querySelectorAll(`td[data-group="${{groupName}}"][data-value]`)
                        );
                        const values = cells
                            .map(cell => parseFloat(cell.dataset.value))
                            .filter(value => !Number.isNaN(value));
                        if (!values.length) return;

                        const min = Math.min(...values);
                        const max = Math.max(...values);
                        const denom = max - min || 1;
                        const low = [236, 242, 234];
                        const high = [252, 228, 230];

                        cells.forEach(cell => {{
                            const value = parseFloat(cell.dataset.value);
                            if (Number.isNaN(value)) return;
                            const t = Math.pow((value - min) / denom, exponent);
                            const r = Math.round(low[0] + (high[0] - low[0]) * t);
                            const g = Math.round(low[1] + (high[1] - low[1]) * t);
                            const b = Math.round(low[2] + (high[2] - low[2]) * t);
                            cell.style.backgroundColor = `rgb(${{r}}, ${{g}}, ${{b}})`;
                        }});
                    }};

                    applyGroup('nar', 1.15);
                    applyGroup('ar', 1.4);
                }});
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

                applyHeatmap();
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
                <div class="paper-venue">Anonymous 2026</div>
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
            <div style="font-weight: 600; margin-bottom: 10px;">Citation</div>
            <div class="citation-block">
@article{{GearVDM,
  title={{{paper_title}}},
  author={{{authors_string}}},
  journal={{Conference Name}},
  year={{2026}}
}}
            </div>
        </div>
    </div>
    
    <div id="clustrmaps-widget-container">
        <script type="text/javascript" id="clustrmaps" src="//clustrmaps.com/map_v2.js?d=EakYmNC57ROvcmK4DT-NyOywRN9Y4G9Bh0BWI7qmXJ8&cl=ffffff&w=a"></script>
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
    for i, (name, indices, author_url) in enumerate(AUTHORS):
        sup_str = ",".join([str(idx + 1) for idx in indices])
        if author_url:
            author_label = f'<a class="author-link" href="{author_url}" target="_blank" rel="noopener">{name}</a>'
        else:
            author_label = name
        authors_html += f'<span class="author-span">{author_label}<sup>{sup_str}</sup></span>'
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

            valid_subs = [
                d for d in sub_datasets
                if d in found_datasets or d in DATASET_DESCRIPTIONS
            ]
            
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

        category_desc = DATASET_DESCRIPTIONS.get(category_name, "")
        if category_desc:
            overview_html += (
                f'<div class="dataset-description" style="margin-bottom: 30px; text-align: left;">'
                f'{category_desc}'
                f'</div>'
            )
        
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

                desc = DATASET_DESCRIPTIONS.get(d_name, "")

                if not rel_files:
                    if not desc:
                        continue

                    header_html = ""
                    if is_group:
                        header_html = f'''
                        <div class="overview-section-header">
                            <h4 class="level-3-header">{d_name}</h4>
                        </div>
                        '''

                    section_html = f"""
                    <div class="overview-section" id="section-{d_name}">
                        {header_html}
                        <div class="overview-desc">{desc}</div>
                    </div>
                    """
                    overview_html += section_html
                    continue

                first_video = rel_files[0]
                total_count = len(rel_files)
                
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
