import numpy as np
import os
import requests
import zipfile

from PIL import Image



LON_STEP = 20
LAT_STEP = 20

REQUIRED_IMAGE_PIXELS = 74213**2

URL = "https://storage.googleapis.com/uq-intertidal/" \
    "v1_1/global_intertidal/"

PERIODS = ["1984-1986", "1987-1989", "1990-1992", 
           "1993-1995", "1996-1998", "1999-2001", 
           "2002-2004", "2005-2007", "2008-2010", 
           "2011-2013", "2014-2016"]

DISK_SPACE_PER_PERIOD = 5 # Go



if Image.MAX_IMAGE_PIXELS < REQUIRED_IMAGE_PIXELS:
    Image.MAX_IMAGE_PIXELS = REQUIRED_IMAGE_PIXELS



def download_data(datadir:str,
                  periods:list[str] = None, 
                  makedirs = True) -> None:
    """
    Downloads and extracts the intertidal data from Global 
    Intertidal Change website (www.intertidal.app).

    Downloading all periods is about 0.9 Go, however, 
    after extraction it goes up, about 44.3 Go (very 
    sparse data). You need 5 Go of free space per period.

    This function iterates through a predefined list of 
    time periods, constructs the corresponding download 
    URLs, downloads the zip files for each period, 
    extracts the contents into the specified destination 
    folder, and deletes the zip files after extraction.

    PARAMETERS
    ----------
        (str) datadir: 
            The directory where downloaded files will be 
            extracted.

        (list[str]) periods=None: 
            List of periods to download. If None, download 
            all available periods.

        (bool) makedirs=True: 
            If True and folderpath's directory does not 
            exist, create it.

    RETURNS
    -------
        None

    RAISES
    ------
        MemoryError: 
            Free space on your disk is too small for the 
            periods you want to download.

        ConnectionError:
            Fail to download a period zip file.
    """
    # Create directory if not existing (and makedirs=True)
    if makedirs and not os.path.isdir(datadir):
        os.makedirs(datadir)

    # Take all periods if None, and if empty raise an err
    if periods is None:
        periods = PERIODS
    elif len(periods) <= 0:
        raise ValueError("periods must not be empty.")

    # Check disk free space
    needed_space = DISK_SPACE_PER_PERIOD*len(periods) # Go
    stats = os.statvfs(datadir)
    free_space = (stats.f_frsize * stats.f_bfree
                  ) / (1024 ** 3) # Go
    if free_space < needed_space:
        raise MemoryError(f"To download {len(periods)} "
                           "periods, you need at least "
                          f"{needed_space} Go of free "
                           "space on disk, you only have "
                          f"{free_space} Go for {datadir}.")

    # Iterate over targeted periods to download them
    for period in periods:
        # Skip if a non-empty directory exists
        period_directory = os.path.join(datadir, period)
        if os.path.isdir(period_directory):
            if len(os.listdir(period_directory)) > 0:
                print(f"Non-empty {period} directory found"
                      f", skip {period} download.")
                continue
        
        # Download file
        period_url = f"{URL}{period}.zip"
        local_zip_path = os.path.join(datadir, 
                            os.path.basename(period_url))
        response = requests.get(period_url, stream=True)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to download "
                                  f"{period_url} - Status "
                                   "code: "
                                  f"{response.status_code}")
        
        # Save file
        with open(local_zip_path, 'wb') as f:
            f.write(response.content)

        # Unzip file
        with zipfile.ZipFile(local_zip_path, 'r'
                                ) as zip_ref:
            zip_ref.extractall(datadir)
            print(f"Downloaded {period} period.")

        # Delete zip file after extraction
        os.remove(local_zip_path)



def find_point_cell(lon:float, 
                    lat:float
                    ) -> tuple[int, int]:
    """
    Finds which cell contains a single point (lon, lat).

    The longitude must be between [-180,180] while the 
    latitude must be between [-60,60] (the whole earth 
    latitude is not covered, for more information refer to 
    http://dx.doi.org/10.1038/s41586-018-0805-8)

    PARAMETERS
    ----------
        (float) lon: 
            Longitude of the point.

        (float) lat: 
            Latitude of the point.

    RETURNS
    -------
        (tuple[int,int]) cell_coord:
            Tuple that represents the (cell_lon_min, 
            cell_lat_max) coordinate.

    RAISES
    ------
        ValueError: 
            If the area is outside the valid latitude range 
            or if the longitude is not in valid format.
    """
    # Check that lon and lat are in the available grid
    if not ((-180 <= lon <= 180) and (60 >= lat >= -60)):
        raise ValueError(f"Point ({lon},{lat}) is not in "
            "the available ranges [-180,180] and [-60,60].")
    
    # Find which cell of the grid contains the point
    cell_lon_min = int( (lon//LON_STEP) * LON_STEP )
    cell_lat_max = int( (1 + lat//LAT_STEP) * LAT_STEP )

    return cell_lon_min, cell_lat_max



def find_area_cells(lon_min:float,
                    lon_max:float,
                    lat_min:float,
                    lat_max:float
                    ) -> list[tuple[int,int]]:
    """
    Finds all cells that intersect with a given rectangle 
    area defined by its longitude and latitude boundaries.

    The longitude must be between [-180,180] while the 
    latitude must be between [-60,60] (the whole earth 
    latitude is not covered, for more information refer to 
    http://dx.doi.org/10.1038/s41586-018-0805-8)
    
    PARAMETERS
    ----------
        (float) lon_min: 
            Minimum longitude of the area.

        (float) lat_min: 
            Minimum latitude of the area.

        (float) lon_max: 
            Maximum longitude of the area.

        (float) lat_max: 
            Maximum latitude of the area.
              
    RETURNS
    -------
        (list[tuple[int,int]]) cells:
            A list of tuples, where each tuple 
            represents the (cell_lon_min, cell_lat_max) 
            of a cell that intersects the area.
    """
    # Find the range of cells in longitude and latitude
    lon_cell_min, lat_cell_min = find_point_cell(
                                    lon_min, lat_min)
    lon_cell_max, lat_cell_max = find_point_cell(
                                    lon_max, lat_max)
    lat_cell_min -= LAT_STEP # a cell lat is its max
    
    # Browse all overlapping cells and keep those 
    # containing the area
    cells = []
    for lon in range(lon_cell_min, 
                     lon_cell_max + LON_STEP, 
                     LON_STEP):
        for lat in range(lat_cell_min, 
                         lat_cell_max + LAT_STEP, 
                         LAT_STEP):
            if ((lon < lon_min or lon < lon_max) 
                and lat > lat_min or lat > lat_max):
                cells.append((lon, lat))
    
    return cells



def read_cell(cell_lon_min:int, 
              cell_lat_max:int, 
              datadir:str, 
              period:str = '2014-2016'
              ) -> Image.Image:
    """
    Reads and returns a cell image file based on cell 
    coordinate.

    PARAMETERS
    ----------
        (int) cell_lon_min: 
            Minimum longitude of the cell.

        (int) cell_lat_max: 
            Maximum latitude of the cell.

        (str) datadir: 
            Path to directory containing data.

        (str) period='2014-2016': 
            The data period to read.

    RETURNS
    -------
        (PIL.Image.Image) cell:
            The image object read from the specified file.
    """
    filename = f"{cell_lon_min}_{cell_lat_max}.tif"
    return Image.open(os.path.join(
                            datadir, period, filename))



def crop_cell(cell:Image.Image, 
              cell_lon_min:int, 
              cell_lat_max:int,
              lon_min:float,
              lon_max:float,
              lat_min:float,
              lat_max:float
              ) -> np.ndarray:
    """
    Crops the cell image to the specified area.

    PARAMETERS
    ----------
        (PIL.Image.Image) cell: 
            The cell image to be cropped.

        (int) cell_lon_min: 
            Minimum longitude of the cell.

        (int) cell_lat_max: 
            Maximum latitude of the cell.

        (float) lon_min: 
            Minimum longitude of the area.

        (float) lat_min: 
            Minimum latitude of the area.

        (float) lon_max: 
            Maximum longitude of the area.

        (float) lat_max: 
            Maximum latitude of the area.

    RETURNS
    -------
        (numpy.ndarray) cropped_cell_array:
            The data read from the specified area of the 
            Image, as a numpy array.
    """
    # Modulo LON_STEP and LAT_STEP
    lon_min_rest = max(0, lon_min - cell_lon_min)
    lon_max_rest = min(LON_STEP, lon_max - cell_lon_min)
    lat_min_rest = cell_lat_max - lat_max
    lat_max_rest = cell_lat_max - lat_min

    # Scale to translate from lon and lat to pixels
    lon_scale = cell.width / LON_STEP
    lat_scale = cell.height / LAT_STEP
    min_x = int(lon_min_rest*lon_scale)
    max_x = int(lon_max_rest*lon_scale)
    min_y = int(lat_min_rest*lat_scale)
    max_y = int(lat_max_rest*lat_scale)

    return np.array(
        cell.crop((min_x, min_y, max_x, max_y))
    )



def merge_crops(cropped_cell_arrays:list[np.ndarray],
               cell_coords: list[tuple[int,int]]
               ) -> np.ndarray:
    """
    Merges multiple cropped cell arrays into a single 
    array based on their spatial coordinates.

    PARAMETERS
    ----------
        (list[numpy.ndarray]) cropped_cell_arrays: 
            A list of cropped cell arrays to be merged.

        (list[tuple[int,int]]) cell_coords: 
            A list of tuples containing the cell 
            coordinate (cell_lon_min, cell_lat_max) 
            corresponding to each cropped cell array.

    RETURNS
    -------
        (numpy.ndarray) merged_cropped_cell_array: 
            The merged array combining the cropped cell 
            arrays.

    RAISES
    ------
        ValueError: 
            If the number of cell coordinates does not 
            match the number of cropped cell arrays or 
            if the list is empty.

        NotImplementedError: 
            If the number of cropped cell arrays is not 
            1, 2, or 4. Not 3 because the area is a 
            rectangle. Not more because it would require 
            too much RAM for most use cases.
    """
    n = len(cell_coords)
    mcca = None # merged_cropped_cell_array

    # Be sure that there are crops
    if n <= 0:
        raise ValueError("empty cell_coordinates list")
    elif n != len(cropped_cell_arrays):
        raise ValueError("cropped_cell_arrays must have "
                         "same the length "
                         "as cell_coordinates")
    
    # Nothing to merge with 1 crop
    elif n == 1:
        mcca = cropped_cell_arrays[0]
    
    # Vertical or horizontal stack with 2 crops
    elif n == 2:
        # Same lon means that it is a vertical stack
        if cell_coords[0][0] == cell_coords[1][0]:
            # Stack lower lat below higher lat
            if cell_coords[0][1] > cell_coords[1][1]: 
                mcca = np.vstack(cropped_cell_arrays)
            else:
                mcca = np.vstack(cropped_cell_arrays[::-1])
        # Same lat means that it is an horizontal stack
        elif cell_coords[0][1] == cell_coords[1][1]:
            # Stack lower lon at the left of higher lon
            if cell_coords[0][0] > cell_coords[1][0]: 
                mcca = np.hstack(cropped_cell_arrays[::-1])
            else:
                mcca = np.hstack(cropped_cell_arrays)
    
    # Vertical stack of left side, then right side, 
    # and finally horizontal stack of left and right sides
    # for 4 crops.
    elif n == 4:
        # Find minimum lon and vertically stack them 
        lons = np.array([lon for lon, _ in cell_coords])
        min_lon_args = np.argwhere(lons == lons.min())
        left_side = merge_crops(
                [cropped_cell_arrays[min_lon_args[0][0]],
                cropped_cell_arrays[min_lon_args[1][0]]],
                [cell_coords[min_lon_args[0][0]],
                cell_coords[min_lon_args[1][0]]])
        # Do the same with maximum lon
        other_args = np.array([i for i in range(n) if i not in min_lon_args])
        right_side = merge_crops(
                [cropped_cell_arrays[other_args[0]],
                 cropped_cell_arrays[other_args[1]]],
                [cell_coords[other_args[0]],
                 cell_coords[other_args[1]]])
        # Horizontally stack left and right sides
        mcca = np.hstack([left_side, right_side])

    else:
        raise NotImplementedError("This function works "
            "with 1, 2 or 4 crops. Not 3 because the area "
            "is a rectangle. Not more because it would "
            "require too much RAM for most use cases.")

    return mcca



def get_intertidal_area(lon_min:float,
                        lon_max:float,
                        lat_min:float,
                        lat_max:float, 
                        datadir:str, 
                        period:str='2014-2016'
                        ) -> np.ndarray:
    """
    Retrieves the intertidal area data for the specified 
    area.

    The longitude must be between [-180,180] while the 
    latitude must be between [-60,60] (the whole earth 
    latitude is not covered, for more information refer to 
    http://dx.doi.org/10.1038/s41586-018-0805-8)

    PARAMETERS
    ----------
        (float) lon_min: 
            Minimum longitude of the area.

        (float) lat_min: 
            Minimum latitude of the area.

        (float) lon_max: 
            Maximum longitude of the area.

        (float) lat_max: 
            Maximum latitude of the area.

        (str) datadir: 
            The directory path where the data files are 
            stored.

        (str) period='2014-2016': 
            The data period to retrieve.

    RETURNS
    -------
        (numpy.ndarray) intertidal_area: 
            The array representing the intertidal area for 
            the specified area.
    """
    cell_coords = find_area_cells(lon_min, lon_max,
                                  lat_min, lat_max)
    cropped_cell_arrays = []
    for cell_lon_min, cell_lat_max in cell_coords:
        cell = read_cell(cell_lon_min, cell_lat_max, 
                         datadir, period=period)
        cropped_cell = crop_cell(cell, cell_lon_min, 
                                 cell_lat_max, lon_min,
                                 lon_max, lat_min, lat_max)
        cropped_cell_arrays.append(cropped_cell)

    return merge_crops(cropped_cell_arrays, cell_coords)