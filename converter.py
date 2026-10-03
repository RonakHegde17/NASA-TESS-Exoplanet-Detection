import os
import lightkurve as lk
import pandas as pd

directory = os.path.join(os.path.expanduser("~"), "Desktop", "tess_data")

targets = {
    "LHS 3844 b": "410153553",
    "HD 189733 b": "256364928",
}

for planet_name, id in targets.items():
    fits_path = os.path.join(directory, f"{id}.fits")
    excel_path = os.path.join(directory, f"{id}.xlsx")

    if not os.path.exists(fits_path):
        print(f"{planet_name}: no file found at {fits_path}")
        continue

    lc = lk.read(fits_path).normalize()

    df = pd.DataFrame({
        "time_BJD": lc.time.value,
        "flux": lc.flux.value,
    })

    df.to_excel(excel_path, index=False)
    print(f"{planet_name}: wrote {len(df)} rows to {excel_path}")