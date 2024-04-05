# This script makes use of the Google Street View Static API to generate images given coordinates from the expert annotated set.
# When you run it, you can set the tree condition of which data you would like to capture. Then a folder structure is created for this label in the folder
# "trees" (please create manually if it does not exist). This creates two folders "filtered" and "unfiltered" which both contain an "image" folder and
# a "json" folder, which contains metadata associated to the gsv image.
# In the main loop of the code, filtered data is collected. In the current script it is possible to filter using the amount of days since the last measurement
# It is also possible to filter images from any season you prefer (I.E. spring/summer to ensure leaves are on the trees)
# Our generated dataset has only the spring and summer seasons filtered and the days from inspection value is set at really high on purpose in order to
# Only filter on seasons and not on the amount of time since inspection.

# Note that using the url with the api key costs 7$ per 1000 requests. This means 0.7 cents per use. This can become very expensive really quick
# So please take care when using the link. Perform the first trials on smaller segments of the data. When using a larger dataset, please check if
# you are happy with the results before printing more pictures. Please abort the process if you are not happy with crtl+c.
# We got a budget for 300$ by using the free version. Thus we can use the link 1000*300/7 = 43000 times. Of course it is always a possibility that
# someone else from our team makes an account if this is used up, but lets try to be a little economical.

import numpy as np
import geopandas as gpd
import pandas as pd
import requests
import osmnx as ox
import os
import json
from datetime import datetime
# from shapely.geometry import Point

tree_condition = "Matig"
# tree_condition = "Redelijk"
# tree_condition = "Slecht"
# tree_condition = "Zeer Slecht"
# tree_condition = "Goed"
# tree_condition = "Dood"

print("Generating data for trees with condition: ", tree_condition)

# Path to shapefile
# shapefile = "../TreehealthDataset/bomen.shp"
shapefile = "./data/TreeHealthDataSet/bomen.shp"

# Read the shapefile
gdf = gpd.read_file(shapefile)
pd.set_option('display.max_columns', None)
# print(gdf.head())
# Filter the non entries and any conditions null.
filtered_gdf = gdf[gdf['CONDITIE'].notna() != "null"]
filtered_gdf = filtered_gdf[filtered_gdf['INSPECTIED'].notna()]

# FIlter for the district Voordijkshoorn
# filtered_gdf = filtered_gdf[filtered_gdf['WIJK'] == "14 Voordijkshoorn"]

# For my non native dutch friends: BOOMSORTIM is not dutch but I'm assuming it means species for this context
# If you would like to filter on another species, you can check pinea.app (from the Akshit's link), and fill in that name
# filtered_gdf = gdf[gdf['BOOMSORTIM'] == "Prunus serrulata 'Amanogawa'"] # 20 pictures, 0.14 cents
# filtered_gdf = gdf[gdf['BOOMSORTIM'] == "Prunus 'Spire'"] # 20 pictures, 0.14 cents
# filtered_gdf = filtered_gdf[filtered_gdf['BOOMSORTIM'] == "Acer"] # This one has 90 pictures. Thus !!! WE PAY 70 CENTS !!! when we run this!!!!!!
# filtered_gdf = filtered_gdf[filtered_gdf['BOOMSORTIM'] == "Fraxinus excelsior"] # 2000 PICTURES. RUNNING THIS WHOLE THING WITH NO DISTICT FILTER WOULD COST 14 DOLLARS!
filtered_gdf = filtered_gdf[filtered_gdf['CONDITIE'] == tree_condition]


# Switch dutch coordinate system to the correct format
filtered_gdf = filtered_gdf.to_crs(epsg=4326)
# print(filtered_gdf.head())
# print(filtered_gdf.columns)

# Function to convert date string to datetime object
def parse_inspection_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

# Apply the parsing function to the 'INSPECTIED' column
filtered_gdf['ParsedInspectionDate'] = filtered_gdf['INSPECTIED'].apply(parse_inspection_date)
filtered_gdf[filtered_gdf['INSPECTIED']!=None]

def create_directories(base_dir, tree_condition):
    tree_condition_dir = os.path.join(base_dir, tree_condition)

    filtered_dir = os.path.join(tree_condition_dir, "filtered")
    unfiltered_dir = os.path.join(tree_condition_dir, "unfiltered")

    filt_image_dir = os.path.join(filtered_dir, "images")
    filt_json_dir = os.path.join(filtered_dir, "json")

    unfilt_image_dir = os.path.join(unfiltered_dir, "images")
    unfilt_json_dir = os.path.join(unfiltered_dir, "json")

    os.makedirs(filtered_dir, exist_ok=True)
    os.makedirs(unfiltered_dir, exist_ok=True)
    os.makedirs(filt_image_dir, exist_ok=True)
    os.makedirs(filt_json_dir, exist_ok=True)
    os.makedirs(unfilt_image_dir, exist_ok=True)
    os.makedirs(unfilt_json_dir, exist_ok=True)

    return filt_image_dir, filt_json_dir


def get_season(date):
    year = date.year
    seasons = {
        'spring': (datetime(year, 3, 21), datetime(year, 6, 20)),
        'summer': (datetime(year, 6, 21), datetime(year, 9, 22)),
        'autumn': (datetime(year, 9, 23), datetime(year, 12, 20)),
        'winter': (datetime(year, 12, 21), datetime(year, 3, 20))
    }
    
    for season, (season_start, season_end) in seasons.items():
        if season_start <= date <= season_end:
            return season

    # Default to winter if the date isn't in the other ranges (for dates like 12/31)
    return 'winter'


image_directory, json_directory = create_directories("./trees", tree_condition)

# API key
api_key = 'AIzaSyBAKyfH5aK83gKB-nY6vVn1ALtt9zXb2xM'
# print(filtered_gdf['INSPECTIED'].head())

print("Number of data points:", filtered_gdf.shape[0])
print("Running this whole set will cost ", filtered_gdf.shape[0]*7/1000, " Dollars!")
i=0
metadata_notok = 0
unfiltered_images_saved = 0
treenumber = 0
for index, row in filtered_gdf.iterrows():
    if i % 100 == 0:
        print(i, "/", filtered_gdf.shape[0], " iterations passed")
    # Assuming the CRS is already in latitude and longitude (EPSG:4326)
    lat, lon = row.geometry.y, row.geometry.x
    inspection_date = row['ParsedInspectionDate']

    # Construct url
    url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={api_key}"
    response = requests.get(url)
    metadata = response.json()
    if metadata['status'] == 'OK':
        treenumber += 1
        # Google Street View metadata provides the date in 'YYYY-MM' format
        capture_date = datetime.strptime(metadata['date'], '%Y-%m')
        # Check if the capture date is within your desired time frame of the inspection date
        # print("GSV capture date: ", capture_date, "; Inspection date: ", inspection_date, "; Time difference: ", abs((capture_date - inspection_date).days), " Days")
        image_url = f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lon}&key={api_key}"
        if image_url:
            image_response = requests.get(image_url)
        if(inspection_date != None):
            # print(capture_date)
            # print(inspection_date)

            # HERE YOU CAN PERFORM FILTERING
            if abs((capture_date - inspection_date).days) <= 122730:  # Picture taken at least 1000000 years ago
                season = get_season(capture_date)
                if(season == 'spring' or season == 'summer'): # Check if picture is made during spring or summer

                    # Save the image in filtered
                    image_filename = f"trees/{tree_condition}/filtered/images/tree_{treenumber}.jpg"
                    with open(image_filename, 'wb') as file:
                        file.write(image_response.content)

                    # Save the json in filtered
                    json_filename = f"trees/{tree_condition}/filtered/json/tree_{treenumber}.json"
                    with open(json_filename, 'w') as json_file:
                        json.dump(metadata, json_file, indent=4)
        # print(image_response.status_code)
                        
        # Save the image in unfiltered
        image_filename = f"trees/{tree_condition}/unfiltered/images/tree_{treenumber}.jpg"
        with open(image_filename, 'wb') as file:
            unfiltered_images_saved += 1
            if unfiltered_images_saved % 100 == 0:
                print(unfiltered_images_saved, " Unfiltered images saved")
            file.write(image_response.content)

        # Save the json
        json_filename = f"trees/{tree_condition}/unfiltered/json/tree_{treenumber}.json"
        with open(json_filename, 'w') as json_file:
            json.dump(metadata, json_file, indent=4)
    else:
        metadata_notok += 1
        if metadata_notok % 100 == 0:
            print("metadata status not OK for ", metadata_notok, " times")
    i+=1

