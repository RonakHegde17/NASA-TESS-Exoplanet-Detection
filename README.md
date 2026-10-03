# NASA-TESS-Exoplanet-Detection

# Introduction
In 1992, we confirmed the existence of two planets orbiting the pulsar PSR B1257+12, and we have since confirmed thousands of exoplanets in the following years. Today, astronomers believe that the vast majority of star systems contain at least one exoplanet. 

There are *hundreds of billions* of stars in the Milky Way, meaning there are potentially *trillions* of worlds in the Milky Way alone, so how do we look for them?
# Methodology
When looking for objects in the universe such as galaxies and stars, we are often able to detect them because of their size and brightness, but the majority of exoplanets are tiny and dark in comparison.

Instead of directly imaging the exoplanet, we can indirectly look for them. Stars are continuously radiating light that we can detect with photometers. When an exoplanet passes between a star and our line of sight, a portion of this light is blocked.

Since planets orbit at a regular interval, assuming the orbit of the planet is aligned with our line of sight, we will detect a relatively consistent pattern of dimming from the star, telling us that there is *something* (potentially a planet) blocking its light.
<img width="1041" height="443" alt="image" src="https://github.com/user-attachments/assets/f58ae9a6-3c12-4627-8a41-86805ad92a53" />
*Source: [University of Nebraska–Lincoln](https://astro.unl.edu/newRTs/Transits/background/Transit1.html)*

This is the *transit* method of detecting exoplanets. Using data from the NASA's TESS *(Transiting Exoplanet Survey Satellite)*, we can analyze a star's brightness for periodic dips and extrapolate information about potential planets around it. 

**For this project, we will focus on the stars LHS 3844 and HD 189733 A, and locating their respective exoplanets LHS 3844 b and HD 189733 b.** 

**LHS 3844 b is a rocky super-Earth planet that orbits its host star in just over 11 hours, while 
HD 189733 b is a hot Jupiter-sized planet that orbits extremely close to its host star. It's also famous for raining molten glass sideways.

NOTE: This is not the only method of detecting exoplanets
# Dependencies 
We will need the following packages

```
pip install lightkurve numpy matplotlib pandas openpyxl astroquery
```
## Optional 
```
pip install oktopus autograd
```
# Downloading the Dataset
We can download the light curves for each star from the MAST archive and save them to the desktop using the lightkurve library. The numbers are the stars' respective IDs in the archive.

<img width="770" height="117" alt="image" src="https://github.com/user-attachments/assets/baff0baf-4b84-43a9-ae8a-b54d945cb451" />

### Code
```python
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
```



# Converting The Dataset to an Excel Spreadsheet
We can convert the light curve data from a FIT file into a excel spreadsheet using the lightkurve and pandas libraries


<img width="770" height="188" alt="image" src="https://github.com/user-attachments/assets/02c4c9e9-b813-4faa-bf4d-6bc6bca51e9f" />


We can now view the raw data for brightness over time for both stars. We will look at LHS 3844 as an example.

time_BJD is the Barycentric Julian Date. Since the earth is moving around the sun, light from distant stars will arrive at different times depending on our location. time_BJD corrects for this and is measured in days.

flux is the measured brightness. Since we are only interested in the change in brightness, the units don't matter and we can normalize the median around 1.0. This will allow us to more easily view peaks and dips in the brightness
<img width="1075" height="980" alt="image" src="https://github.com/user-attachments/assets/34f740d3-9843-4088-8f42-4fccbab5cefa" />


### Code
```python
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
```

# Analysis
Using our converted excel files, we can plot one of the stars light curves to obtain the following graph
<img width="1397" height="587" alt="image" src="https://github.com/user-attachments/assets/2c9597fc-61bf-45eb-a605-04939581bd3b" />


This is the light curve of the star LHS 3844. It's cluttered, but we can see a visible gap at ~1338 days and a possible gap at ~1348 days. 

However, this graph is pretty useless by itself. We see that the brightness is oscillating, but we can't extract any meaningful information about what may be causing it and what its properties are yet. We have to either modify the plot or perform further analysis for any insight.

If we knew the orbital period of the planet, we could identify the exact points in time that correspond to decreases and increases in brightness, so this is a good starting point for our analysis.

During the planet's transiting, we should observe a sharply defined decrease (planet moves in front of the star) and then increase in detected light (planet moves past the star), producing a *box-pattern* that repeats with each transit. We can try the **BLS** (Box Least Squares) method to find the period of the exoplanet. 


## Finding the Orbital Period with BLS
BLS tests several transit durations for thousands of periods over a given amount of days, identifying which one produces the most clearly defined box-pattern. It is essentially a brute-force calculation of what the most statistically likely period of an exoplanet is.

Since the duration tested must be shorter than the period tested, we can't test the entire time range in a single go.  We will need to perform two separate BLS tests

BLS short - Tests 20,000 periods from 0.1 to 2 days with 10 transit durations from 0.01 to 0.08 days
BLS long - Tests 20,000 periods from 2 to 50 days with 10 transit durations from 0.05 to 0.5 days.

This will give us 4 periods, one short and one long result for each both stars. We can then compare the statistical power of each to find out which period is most likely correct if there *were* an exoplanet around the star.

We can also calculate the transit depth, which is the fraction of the stars total light blocked by the planet. This will be useful for future calculations.

## Results of BLS
Performing the BLS tests produce the following orbital periods

<img width="822" height="201" alt="image" src="https://github.com/user-attachments/assets/3d7c8bf0-b2a8-4497-ab62-1c1d316ddd57" />


## Verifying Transit by Folding Dataset

Since the orbital period of the planet is cyclical, instead of using time_BJD which records all transits at separate points in time, we can use the *phase*. 

This will use the fraction of the orbital cycle completed as the independent variable, meaning that we plot all transits at the same location on the graph. We will use the calculated best period from the previous BLS test as the standard. This process is called *folding* the dataset.

The location of the exoplanet during transiting will be designated as phase = 0


<img width="1735" height="571" alt="image" src="https://github.com/user-attachments/assets/4f17af00-b7e4-445c-a8a0-ab5d847e01e5" />

<img width="1746" height="575" alt="image" src="https://github.com/user-attachments/assets/aee21597-43c6-4c37-a92c-aef7c0555eea" />

We can see that after folding the dataset, there is a visible decrease in brightness across all transits. This is strong evidence of an object that is passing in front of the star and blocking its light. 

However, we don't know if a *planet* is the object passing in front of the star. It's possible that we are looking at a binary star system and the periodic dips in brightness are caused by the transiting of its neighbor star.

NOTE: The graph for HD 189733 is much smoother because its much brighter than LHS 3844. This allows us to see more of the gradual change in brightness as the planet passes the edge of the star.

## Evidence against a Binary Star System

Thinking about this conceptually, we expect that a planet passing in front of the star will cause approximately the same change in brightness every single time, as the planet is far smaller.

However, in a binary star system, the stars will be much more comparable in size. They will orbit *around* each other (around the common center of mass)

The bigger star will be producing most of the light observed, so when the smaller one passes in front it, we will notice a drop in brightness, but when the larger star passes in front of the smaller one, we don't expect to see any significant drop in brightness.

Since the transiting object alternates between the bigger and smaller star, we can split the transits into odds (#1, #3, #5...) and evens (#2, #4, #6...). and compare the amount of light blocked (our calculated depth from the BLS test), between each.

As a general rule, if the difference between the odd and even transits is statistically insignificant, it is consistent with the pattern of an exoplanet and not a binary star system. This requires storing error bars for all data points, so for convenience sake, we will use a threshold of 30% similarity.

## Results of Odd/Even Transit Test

Performing the Odd/Even Transit Test results in the following output

<img width="815" height="167" alt="image" src="https://github.com/user-attachments/assets/302d29e3-b016-4a0b-a29c-7d0a670a903c" />

<img width="877" height="168" alt="image" src="https://github.com/user-attachments/assets/00adad74-592d-4645-af92-683fa8ec199e" />


We see that both stars display similar even and odd transit depths, which is consistent with the presence of a planet

##  Calculating Exoplanet Radius
As of now, we have a strong case for believing both stars are being orbited by a planet, but as a final check, we can estimate the radius of the orbiting object.

<img width="1169" height="698" alt="image" src="https://github.com/user-attachments/assets/5035e55d-1d5d-43bb-a98f-e08796efae75" />

*Source: [NASA.gov](https://science.nasa.gov/photojournal/perseverance-views-a-transit-of-deimos/?utm_medium=organic&utm_source=yandexsmartcamera)*

Since both the star and its orbiting object appear to us as circles, the fraction of total light blocked (depth) will be equivalent to the orbiting objects cross area divided by the stars area.

depth = $A_{Object} / A_{Star}$

  $A = {\pi}R^2$

depth = $R^2_{Object} / R^2_{Star}$ 

$R_{Object}$  = $R_{Star} * \sqrt{depth}$

Using known information about each star's radius, we can calculate the radius of their orbiting objects and compare them to the radius of Earth for classification. 

### LHS 3844
<img width="525" height="85" alt="image" src="https://github.com/user-attachments/assets/ecc65614-9865-4b74-8070-f1b599988535" />

### HD 189733 A
<img width="415" height="75" alt="image" src="https://github.com/user-attachments/assets/a85e2e74-5e41-4a17-a0e6-8734a7d3332e" />

The object orbiting LHS 3844 has a radius 1.32 times that of Earth, making it a super-Earth.

The object orbiting HD 189733 A has a radius 12.08 times that of earth, making it a Jupiter-sized gas giant. Since it completes an orbital cycle in just over 2 days, we have evidence to believe this planet is a *hot jupiter*, a high-temperature and massive gas giant that orbits extremely close to its star.



# Conclusion 
In conclusion, we have downloaded publicly available data from NASAs TESS and provided strong evidence for the existence of two planets beyond the solar system.

We detected changes in brightness associated with planetary transits, found their orbital periods using the BLS test, provided strong evidence against a false positive due to a binary star system, and calculated the approximate size of each planet.

**We have found LHS 3844 b, a rocky super-Earth**

Orbital Period: 11.11 hours,

Published Value: 11.1 hours, 

Radius: 1.32 Earth radii,

Published Value: 1.303 Earth radii, 

 
 **We have also found HD 189733 b, a hot Jupiter**
 
Orbital Period: 2.218 days,

Published Value: 2.21857 days,

Radius: 12.08 Earth radii,

Published Value: 12.67 Earth radii
 	


### Code
```python
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

    print(f"\nTARGET: {planet_name}   (host star TIC {id})")  

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

    print(f"Best period:   {best_period:.5f}")
    print(f"Transit depth: {depth:.5f}  ({depth * 100:.3f}% of starlight blocked)")



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

    print(f"Odd-transit depth:  {odd_depth:.5f}")
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

    if planet_radius_rearth < 4:

        print("Consistent with a rocky/super-Earth sized planet.")
        
    elif planet_radius_rearth < 4:

        print("Consistent with a mini-Neptune")

    elif planet_radius_rearth < 11:

        print("Consistent with an ice giant planet (Uranus & Neptune).")

    else:

        print("Consistent with a Jupiter-sized planet")

print("\nAnalysis Complete")
```


