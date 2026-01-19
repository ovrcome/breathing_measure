"""
Shimmer + Inhale CSV Join with PPG Overlay using Functions

Author: Rebekah Au
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ---------------- CONFIG ----------------
TIMESTAMP = "2026-01-19_03.57.42"
SESSION = '20'

SHIMMER_CSV = rf"C:\Users\beks9\Documents\oVRcome\Breathing\breathing_measure\data\{TIMESTAMP}\DefaultTrial_Session{SESSION}_Shimmer_6815_Calibrated_SD.csv"
BREATHING_CSV = rf"C:\Users\beks9\Documents\oVRcome\Breathing\breathing_measure\data\{TIMESTAMP}\inhale_{TIMESTAMP}.csv"
OUTPUT_FOLDER = f"data/{TIMESTAMP}"
OUTPUT_FILENAME = f"shimmer_with_inhale_{TIMESTAMP}.csv"
PLOTS_FOLDER = 'plots'

PPG_COLUMN = "Shimmer_6815_PPG_A13_CAL"
TIMESTAMP_COLUMN = "Shimmer_6815_Timestamp_Unix_CAL"

PPG_THRESHOLD = 10         # mV, remove initial low PPG values
INHALE_OVERLAY_SCALE = 0.8    # scale inhale overlay to 80% of PPG max

# ---------------- FUNCTIONS ----------------

def read_shimmer_csv(filepath):
    """
    Read Shimmer CSV with:
    - sep= line
    - tab delimiter
    - header row
    - units row
    """
    # Always skip first two rows: sep= and units
    shimmer = pd.read_csv(
        filepath,
        sep="\t",
        skiprows=[0, 2]
    )

    shimmer.columns = (
        shimmer.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    return shimmer

def trim_initial_ppg(shimmer, ppg_column, ppg_threshold=PPG_THRESHOLD):
    """Trim all initial PPG values below threshold."""
    mask = shimmer[ppg_column] >= ppg_threshold
    if not mask.any():
        raise ValueError("No PPG values above threshold")
    first_idx = np.argmax(mask.values)  # index of first True
    return shimmer.loc[first_idx:].reset_index(drop=True)


def create_inhale_signal(shimmer, breathing, timestamp_column):
    """Vectorised creation of binary inhale and inhale_id columns."""
    shimmer["inhale"] = 0
    shimmer["inhale_id"] = -1

    inhale_events = breathing[breathing["event"] == "inhale"][["start_epoch", "end_epoch"]].to_numpy()
    times = shimmer[timestamp_column].values / 1000.0  # convert ms to sec if needed
    shimmer["epoch_sec"] = times

    # Vectorised assignment
    for i, (start, end) in enumerate(inhale_events):
        mask = (times >= start) & (times <= end)
        shimmer["inhale"].values[mask] = 1
        shimmer["inhale_id"].values[mask] = i

    return shimmer

def save_shimmer_csv(shimmer, output_folder, output_filename):
    """Save joined Shimmer CSV and ensure folder exists."""
    os.makedirs(output_folder, exist_ok=True)
    save_path = os.path.join(output_folder, output_filename)
    shimmer.to_csv(save_path, index=False)
    print(f"Joined CSV saved to {save_path}")
    return save_path

def plot_ppg_inhale(shimmer, ppg_column, overlay_scale=INHALE_OVERLAY_SCALE):
    os.makedirs(PLOTS_FOLDER, exist_ok=True)

    # Make a copy of time so we don't alter original
    time_sec = shimmer["epoch_sec"].values - shimmer["epoch_sec"].values[0]

    plt.figure(figsize=(12, 4))
    plt.plot(time_sec, shimmer[ppg_column], label="PPG")

    # Only scale inhale if PPG has valid max
    max_ppg = shimmer[ppg_column].max()
    if np.isnan(max_ppg) or max_ppg == 0:
        inhale_scale = 1
    else:
        inhale_scale = max_ppg * overlay_scale

    plt.plot(
        time_sec,
        shimmer["inhale"] * inhale_scale,
        drawstyle="steps-post",
        alpha=0.5,
        label="Inhale"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("PPG / Inhale")
    plt.title("PPG Signal with Inhale Overlay")
    plt.legend()
    plt.tight_layout()

    save_path = os.path.join(PLOTS_FOLDER, f"ppg_inhale_overlay_{TIMESTAMP}.png")
    plt.savefig(save_path, dpi=300)
    plt.close()

    print(f"Plot saved to {save_path}")




# ---------------- MAIN WORKFLOW ----------------

def main():
    # Step 1: Read CSVs
    shimmer = read_shimmer_csv(SHIMMER_CSV)
    
    breathing = pd.read_csv(BREATHING_CSV)
    breathing["start_epoch"] = breathing["start_epoch"].astype(float)
    breathing["end_epoch"] = breathing["end_epoch"].astype(float)

    # Step 2: Trim initial low PPG
    shimmer = trim_initial_ppg(shimmer, PPG_COLUMN)

    # Step 3: Create inhale signal
    shimmer = create_inhale_signal(shimmer, breathing, TIMESTAMP_COLUMN)

    # Step 4: Save CSV
    save_shimmer_csv(shimmer, OUTPUT_FOLDER, OUTPUT_FILENAME)

    # Step 5: Sanity check
    print("Inhale value counts:")
    print(shimmer["inhale"].value_counts())

    # Step 6: Plot
    plot_ppg_inhale(shimmer, PPG_COLUMN)

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
