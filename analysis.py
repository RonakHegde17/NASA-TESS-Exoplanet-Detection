import os
import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from astroquery.mast import Catalogs

directory = os.path.join(os.path.expanduser("~"), "Desktop", "tess_data")

targets = {
    "LHS 3844 b": "410153553",
    "HD 189733 b": "256364928",
}

for planet_name, id in targets.items():

    print(f"\nTARGET: {planet_name}   (host star TIC {id})")


    fits_path = os.path.join(directory, f"{id}.fits")
    
    if not os.path.exists(fits_path):
        print(f"No dataset found at {fits_path}, Use downloader.py first")
        continue

    lc = lk.read(fits_path).remove_nans().normalize().flatten(window_length=401)


    #BLS Test (Finding Orbital Period)
    
    bls_short = lc.to_periodogram(method="bls",
    period=np.linspace(0.1, 2, 20000),
    duration=np.linspace(0.01, 0.08, 10))
    bls_long = lc.to_periodogram(method="bls",
    period=np.linspace(2, 50, 20000),
    duration=np.linspace(0.05, 0.5, 10))

    if bls_short.max_power > bls_long.max_power:
        bls = bls_short
        print(f"Short-period signal wins: {bls_short.period_at_max_power:.5f} "
              f"(power={bls_short.max_power:.1f}) vs long-period "
              f"{bls_long.period_at_max_power:.5f} (power={bls_long.max_power:.1f})")
    else:
        bls = bls_long
        print(f"Long-period signal wins: {bls_long.period_at_max_power:.5f} "
              f"(power={bls_long.max_power:.1f}) vs short-period "
              f"{bls_short.period_at_max_power:.5f} (power={bls_short.max_power:.1f})")

    best_period = bls.period_at_max_power
    best_t0 = bls.transit_time_at_max_power
    best_duration = bls.duration_at_max_power
    depth = bls.depth_at_max_power

    print(f"Best period:   {best_period:.5f}")
    print(f"Transit depth: {depth:.5f}  ({depth * 100:.3f}% of starlight blocked)")

    #Folding Plot
    
    folded_lc = lc.fold(period=best_period, epoch_time=best_t0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))
    lc.plot(ax=ax1, title=f"{planet_name} - raw light curve")
    folded_lc.scatter(ax=ax2, s=2, title=f"{planet_name} - folded at {best_period:.4f}")
    ax2.set_xlim(-4 * best_duration.value, 4 * best_duration.value)
    plt.tight_layout()
    plt.show()

    #Odd/Even Transit Depth Check (Ruling out Binary Star System)
    
    in_transit = np.abs(folded_lc.phase.value) < (best_duration.value / 2)
    cycle = folded_lc.cycle

    odd_depth = 1 - np.nanmedian(folded_lc.flux.value[in_transit & (cycle % 2 == 1)])
    even_depth = 1 - np.nanmedian(folded_lc.flux.value[in_transit & (cycle % 2 == 0)])

    print(f"Odd-transit depth:  {odd_depth:.5f}")
    print(f"Even-transit depth: {even_depth:.5f}")
    if abs(odd_depth - even_depth) < 0.3 * depth:
        print("Not consistent with a binary star system")
    else:
        print("Consistent with a binary star system")
    
    
    #Radius Calculation
    
    RSUN_TO_REARTH = 109.2 
    
    tic_row = Catalogs.query_criteria(catalog="Tic", ID=id)[0]
    star_radius_rsun = tic_row["rad"]

    planet_radius_rearth = star_radius_rsun * np.sqrt(depth) * RSUN_TO_REARTH
    print(f"Host star radius: {star_radius_rsun:.3f} solar radii")
    print(f"Estimated planet radius: {planet_radius_rearth:.2f} Earth radii")

    if 1 < planet_radius_rearth < 2:
        print("Consistent with a rocky/super-Earth sized planet.")
    elif planet_radius_rearth < 4:
        print("Consistent with a mini-Neptune")
    elif planet_radius_rearth < 11:
        print("Consistent with an ice giant planet (Uranus & Neptune).")
    else:
        print("Consistent with a Jupiter-sized planet")

print("\nAnalysis Complete")