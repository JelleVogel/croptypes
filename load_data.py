# This script makes use of the Google Street View Static API to generate images given coordinates from the expert annotated set
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
import math
# from shapely.geometry import Point

# Path to shapefile
shapefile = "TreehealthDataset/bomen.shp"

# Read the shapefile
gdf = gpd.read_file(shapefile)
pd.set_option('display.max_columns', None)
# print(gdf.head())
# Filter the non entries and any conditions null.
filtered_gdf = gdf[gdf['CONDITIE'].notna() != "null"]

# FIlter for the district Voordijkshoorn
filtered_gdf = filtered_gdf[filtered_gdf['WIJK'] == "14 Voordijkshoorn"]


# For my non native dutch friends: BOOMSORTIM is not dutch but I'm assuming it means species for this context
# If you would like to filter on another species, you can check pinea.app (from the Akshit's link), and fill in that name
# filtered_gdf = gdf[gdf['BOOMSORTIM'] == "Prunus serrulata 'Amanogawa'"] # 20 pictures, 0.14 cents
# filtered_gdf = gdf[gdf['BOOMSORTIM'] == "Prunus 'Spire'"] # 20 pictures, 0.14 cents
# filtered_gdf = filtered_gdf[filtered_gdf['BOOMSORTIM'] == "Acer"] # This one has 90 pictures. Thus !!! WE PAY 70 CENTS !!! when we run this!!!!!!
filtered_gdf = filtered_gdf[filtered_gdf['BOOMSORTIM'] == "Fraxinus excelsior"] # 2000 PICTURES. RUNNING THIS WHOLE THING WITH NO DISTICT FILTER WOULD COST 14 DOLLARS!
print("Number of data points:", filtered_gdf.shape[0])
print("Running this whole set will cost ", filtered_gdf.shape[0]*7/1000, " Dollars!")

# Switch dutch coordinate system to the correct format
filtered_gdf = filtered_gdf.to_crs(epsg=4326)
# print(filtered_gdf.head())



# Define a function to construct the API URL
def construct_url(heading, lat, lon, api_key):
    fov = 90
    return f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lon}&heading={heading}&fov={fov}&key={api_key}"


# Function copied from getAllRoadPtsBearing.py from the github
def computeBearing(fro, to):
    y = math.sin(to[1]-fro[1]) * math.cos(to[0])
    x = math.cos(fro[0])*math.sin(to[0]) - math.sin(fro[0])*math.cos(to[0])*math.cos(to[1]-fro[1])
    θ = math.atan2(y, x)
    brng = (θ*180/math.pi + 360) % 360
    return brng


# Function to determine the heading of the car
def heading_compensation(lat1, lon1):
    # Get the nearest networkx graph within 30 meters
    G = ox.graph_from_point((lat1, lon1), dist=300, network_type='all')

    # See here a failed attempt to make the dataset generation more efficient.
    # if len(G.nodes) == 0:
    #     G = ox.graph_from_point((lat1, lon1), dist=300, network_type='all')

    # Find the nearest node in the graph to the point
    # Note that I do not know if this will result in looking trough the windshield or the back of the car, 
    # however it does not matter since we are interested in both looking to the left and looking to the right.
    nearest_node = ox.distance.nearest_nodes(G, lon1, lat1)

    # Get the lat and lon of the nearest node (street point)
    lat2, lon2 = G.nodes[nearest_node]['y'], G.nodes[nearest_node]['x']

    heading = computeBearing([lat1,lon1],[lat2,lon2])

    # # Convert latitude and longitude from degrees to radians
    # lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # dlat = lat2 - lat1

    # x = math.sin(dlat) * math.cos(lat2)
    # y = math.cos(lon1) * math.sin(lon2) - (math.sin(lon1) * math.cos(lon2) * math.cos(dlat))
    # initial_bearing = math.atan2(x, y)

    # # Convert bearing from radians to degrees and normalize
    # heading = math.degrees(initial_bearing)

    return heading



# API key
api_key = 'AIzaSyAes1mHa3VTn9T3hMUNJhlnJ_7DS4XT5so'
for side in {-90, 90}:
    for index, row in filtered_gdf.iterrows():
        # Assuming the CRS is already in latitude and longitude (EPSG:4326)
        lat, lon = row.geometry.y, row.geometry.x

        heading = heading_compensation(lat, lon)
        heading = heading + side # +/- 90 deg
        # Construct URL
        url = construct_url(heading, lat, lon, api_key)

        # Make the request
        response = requests.get(url)

        if response.status_code == 200:
            # Construct a file name using ELEMENTNUM and save the image
            filename = f"trash/tree_{row['ELEMENTNUM']}_{heading}.jpg" # Set to trash when testing
            with open(filename, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to fetch image for tree {row['ELEMENTNUM']}")
