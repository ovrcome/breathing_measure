"""
Programme to record inhale events using the SPACE key only.

Records a single ENTER key press at the start to allow
synchronisation with Shimmer data.

Produces a UTC time-series representing how long the key was held.

Author: Rebekah Au
Date: January 2026
"""

from datetime import datetime, timezone
import pandas as pd
from pynput import keyboard 
import os


# ---------------- CONFIG ----------------
TIMESTAMP = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H.%M.%S')
OUTPUT_FOLDER = f"data/{TIMESTAMP}"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
OUTPUT_CSV = os.path.join(OUTPUT_FOLDER, f"inhale_{TIMESTAMP}.csv")


# ---------------- STATE ----------------
key_press_time = None
sync_recorded = False
events = []


# ---------------- HELPERS ----------------
def utc_now():
    return datetime.now(timezone.utc)


# ---------------- CALLBACKS ----------------
def on_press(key):
    global key_press_time, sync_recorded

    # Record ENTER once for sync
    if key == keyboard.Key.enter and not sync_recorded:
        t = utc_now()
        events.append({
            "event": "sync_start",
            "start_time_utc": t.isoformat(),
            "end_time_utc": t.isoformat(),
            "start_epoch": t.timestamp(),
            "end_epoch": t.timestamp(),
            "duration_sec": 0.0
        })
        sync_recorded = True
        print(f"[SYNC] ENTER pressed at {t.isoformat()}")

    # SPACE = inhale start
    if key == keyboard.Key.space and key_press_time is None:
        key_press_time = utc_now()


def on_release(key):
    global key_press_time

    # SPACE = inhale end
    if key == keyboard.Key.space and key_press_time is not None:
        start_time = key_press_time
        end_time = utc_now()
        key_press_time = None

        events.append({
            "event": "inhale",
            "start_time_utc": start_time.isoformat(),
            "end_time_utc": end_time.isoformat(),
            "start_epoch": start_time.timestamp(),
            "end_epoch": end_time.timestamp(),
            "duration_sec": (end_time - start_time).total_seconds()
        })

    # ESC = stop recording
    if key == keyboard.Key.esc:
        return False


# ---------------- MAIN ----------------
def main():
    print("Recording inhale events (UTC timestamps)")
    print("ENTER = sync start | SPACE = inhale | ESC = stop")
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    df = pd.DataFrame(events)
    df.to_csv(OUTPUT_CSV, index=False)

    print("\nRecording stopped.")
    print(df)
    print(f"\nSaved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
