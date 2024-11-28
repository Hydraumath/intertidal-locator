# Intertidal Locator

An intertidal area is the coastal zone that lies between the high tide and low tide marks, where the land is exposed to air at low tide and submerged under water at high tide.

The intertidal-locator Python library allows to **extract** an **image** of a **specified** **area** (2 longitude and latitude couples) from [Global Intertidal Change](https://www.intertidal.app) data based on [The global distribution and trajectory of tidal flats](http://dx.doi.org/10.1038/s41586-018-0805-8). 

A **pixel**'s value of that image is **1** if it is **in** an **intertidal** area, 0 otherwise.


## Data

The image collection consists consists of a time-series of **11** global **maps** of tidal flats at **30m** **pixel** **resolution** for set time-periods (1984-1986; 1987-1989; 1990-1992; 1993-1995; 1996-1998; 1999-2001; 2002-2004; 2005-2007; 2008-2010; 2011-2013; 2014-2016).

The classification was implemented along the **entire global coastline** between **60° North** and **60° South** from **1 January 1984** to **31 December 2016**. Each image is a cell of 20 longitude width and 20 latitude height of the following **grid**:

| (-180,60)  | ... | (160,60)  |
|------------|-----|-----------|
|    ...     | ... |    ...    |
| (-180,-40) | ... | (160,-40) |


## Documentation

Available [online](https://hydraumath.github.io/intertidal-locator-doc/modules.html), check [./docs](./docs) to build from source.


## Install

Tested with Python >= 3.9.0 and Ubuntu 24.04. 

### From pip

```bash
pip install intertidal-locator
```

### From source

```bash
pip install --upgrade build
```

From `intertidal-locator/`:

```bash
python3 -m build
```

```bash
pip install dist/intertidal_locator-1.0.0-py3-none-any.whl
```


## Use

Get intertidal data for the Pertuis Charentais, in France:

```py
import intertidal_locator as il

# Download 2014-2016 data (do nothing if already exists)
datadir = 'data'
il.download_data(datadir = datadir, 
                 periods = ["2014-2016"], 
                 makedirs = True)

# Extract data for the specified area
intertidal_area = il.get_intertidal_area(
    lon_min = -1.6, lon_max = -0.95,
    lat_min = 45.75, lat_max = 46.4,
    datadir = datadir, period = "2014-2016"
)
```

![Pertuis Charentais intertidal area](./assets/pertuis_charentais.jpg)
