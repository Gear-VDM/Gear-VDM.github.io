"""
Compile and show per-sample error as a broken graph
X-axis: sample index (0, 1, ...)
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# (path, loop index, label for legend)
PATHS: Sequence[Tuple[str, int, str]] = [
	(
		"/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Motion_20/Gear_Motion_Normalize_HighNoise_SCRATCH_7000_MotionLowSCRATCHOnesidedWeight_8000_shift1_1.0_step32b/parsed/eval_summary.json",
		0,
		"Non-auto",
	),
	(
		"/work/koichi/Gear/gear_gen_angle_rad_con_auto/eval_results/Motion_20/Gear_Motion_Normalize_Auto_HighNoise_SCRATCH_7500_MotionLowSCRATCHOnesidedWeight_8000_shift1_1.0_step32b/parsed/eval_summary.json",
		19,
		"Auto",
	),
]

METRIC_KEY = "mechanism_kinematic_tracking_error"
OUTPUT_NAME = "./../../per_sample_kinematic_tracking_error.png"
Y_SCALE = None
Y_MIN = 0.0
Y_PAD_FRAC = 0.08
LINTHRESH_QUANTILE = 0.2
MIN_LINTHRESH = 1e-4
WIDTH_PER_SAMPLE = 0.09
MIN_WIDTH = 6.5
FIG_HEIGHT = 3.2
SHOW_TITLE = False


def _parse_sample_index(sample_name: str) -> Optional[int]:
	match = re.match(r"(\d+)", sample_name)
	if match is None:
		return None
	return int(match.group(1))


def _load_eval_summary(summary_path: str) -> Dict[str, object]:
	with open(summary_path, "r", encoding="utf-8") as f:
		return json.load(f)


def _extract_series(
	summary: Dict[str, object],
	loop_index: int,
	metric_key: str,
) -> Dict[int, float]:
	samples = summary.get("samples", [])
	if not isinstance(samples, list):
		return {}

	series: Dict[int, float] = {}
	next_index = 0
	for record in samples:
		if not isinstance(record, dict):
			continue
		sample_name = str(record.get("sample", ""))
		if loop_index >= 0 and f"_loop_{loop_index}_" not in sample_name:
			continue
		value = record.get(metric_key)
		if not isinstance(value, (int, float)):
			continue
		sample_index = _parse_sample_index(sample_name)
		if sample_index is None:
			while next_index in series:
				next_index += 1
			series[next_index] = float(value)
			next_index += 1
		else:
			series[int(sample_index)] = float(value)
			next_index = max(next_index, sample_index + 1)

	return series


def _merge_indices(series_list: Iterable[Dict[int, float]]) -> List[int]:
	merged: set[int] = set()
	for series in series_list:
		merged.update(series.keys())
	return sorted(merged)


def _compute_linthresh(values: np.ndarray) -> float:
	values = values[np.isfinite(values)]
	if values.size == 0:
		return MIN_LINTHRESH
	positive = values[values > 0]
	if positive.size == 0:
		return MIN_LINTHRESH
	linthresh = float(np.quantile(positive, LINTHRESH_QUANTILE))
	return max(MIN_LINTHRESH, linthresh)


def _plot_scaled_axis(
	x: List[int],
	ys: Sequence[np.ndarray],
	labels: Sequence[str],
	metric_label: str,
	output_path: str,
) -> None:
	all_values = np.concatenate([y[np.isfinite(y)] for y in ys if y.size > 0])
	linthresh = _compute_linthresh(all_values)

	width = max(MIN_WIDTH, WIDTH_PER_SAMPLE * max(1, len(x)))
	fig, ax = plt.subplots(figsize=(width, FIG_HEIGHT))

	for y, label in zip(ys, labels):
		ax.plot(x, y, marker="o", markersize=2.8, linewidth=1.0, label=label)

	if len(x) > 0:
		step = max(1, len(x) // 20)
		ticks = x[::step]
		ax.set_xticks(ticks)

	if Y_SCALE:
		ax.set_yscale(Y_SCALE, linthresh=linthresh)
	if np.isfinite(all_values).any():
		y_max = float(np.nanmax(all_values))
		pad = max(1e-6, abs(y_max) * Y_PAD_FRAC)
		ax.set_ylim(bottom=Y_MIN, top=y_max + pad)

	ax.set_xlabel("sample index")
	ax.set_ylabel(metric_label)
	ax.legend(loc="upper right")
	if SHOW_TITLE:
		ax.set_title("Per-sample error")

	fig.tight_layout(pad=0.2)
	fig.savefig(output_path, dpi=200, bbox_inches="tight", pad_inches=0.02)
	plt.close(fig)


def main() -> None:
	series_list: List[Dict[int, float]] = []
	labels: List[str] = []

	for summary_path, loop_index, label in PATHS:
		summary = _load_eval_summary(summary_path)
		series = _extract_series(summary, loop_index, METRIC_KEY)
		if len(series) == 0:
			raise RuntimeError(f"No samples found for {summary_path}")
		series_list.append(series)
		labels.append(label)

	x = _merge_indices(series_list)
	ys = [np.array([series.get(idx, np.nan) for idx in x], dtype=np.float64) for series in series_list]

	metric_label = METRIC_KEY.replace("mechanism_", "").replace("_", " ")
	output_path = os.path.join(os.path.dirname(__file__), OUTPUT_NAME)
	_plot_scaled_axis(x, ys, labels, metric_label, output_path)
	print(f"Saved scaled plot to: {output_path}")


if __name__ == "__main__":
	main()

