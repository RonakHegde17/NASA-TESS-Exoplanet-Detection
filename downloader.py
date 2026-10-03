import os
import lightkurve as lk

data_dir = os.path.join(os.path.expanduser("~"), "Desktop", "tess_data")
os.makedirs(data_dir, exist_ok=True)


targets = {
    "LHS 3844 b": "410153553",
    "HD 189733 b": "256364928",
}

for planet_name, tic_id in targets.items():
    local_path = os.path.join(data_dir, f"{tic_id}.fits")

    if os.path.exists(local_path):
        print(f"{planet_name}: Already downloaded at {local_path}")
        continue

    print(f"{planet_name}: searching MAST for TIC {tic_id}")
    search_result = lk.search_lightcurve(f"TIC {tic_id}", mission="TESS",
    author="SPOC")
    print(search_result)

    if len(search_result) == 0:
        print(f"{planet_name}: no data found, skipping")
        continue

    print(f"{planet_name}: downloading")
    lc = search_result[0].download()
    lc.to_fits(local_path, overwrite=True)
    print(f"{planet_name}: saved to {local_path}")

print("\nData saved to 'tess_data'")