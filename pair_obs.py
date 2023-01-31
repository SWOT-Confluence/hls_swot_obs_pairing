#!/usr/bin/env python3
"""
Author : Travis Simmons
Date   : 01/31/2023
Purpose: Read in a netcdf and pull related hls images
"""

import argparse
import os
import shutil
import sys
import glob
import subprocess
import netCDF4
import numpy as np
import json
import datetime
import pystac_client
from pystac_client import Client  
from collections import defaultdict    
import json
import geopandas
import pandas as pd


INPUT_DIR = 'mnt/data/input/'

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Rock the Casbah',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-rj',
                        '--reaches_json',
                        help='name of json containing the reach ids',
                        metavar='str',
                        type=str,
                        default='reaches.json')



    return parser.parse_args()



#---------------functions----------------

def find_hls_tiles(point=False, band=False, limit=False, collections = ['HLSL30.v2.0', 'HLSS30.v2.0'], date_range = False):

    STAC_URL = 'https://cmr.earthdata.nasa.gov/stac'


    catalog = Client.open(f'{STAC_URL}/LPCLOUD/')



    try:
        x, y = point[0], point[1]
        # print(x,y)
    except TypeError:
        print("Point must be in the form of [lat,lon]")
        raise

    point = geopandas.points_from_xy([x],[y])
    point = point[0]



    # JOHN - THIS IS WHERE YOU WOULD ADD IN SEARCH PARAMETERS
    if date_range:

        search = catalog.search(
            collections=collections, intersects = point, datetime=date_range)
    else:
        search = catalog.search(
            collections=collections, intersects = point)



    # print(f'{search.matched()} Tiles Found...')


    item_collection = search.get_all_items()

    if limit:
        item_collection = item_collection[:limit]

    if band:
        links = []
        if type(band) == list:
            for i in item_collection:

                for b in band:
                    link = i.assets[b].href
                    # print(link)
                    links.append(link)
        
        else:
            for i in item_collection:
                
                link = i.assets[band].href
                links.append(link)
    
    else:
        links =[]
        for i in item_collection:
            # print()
            # print(i.assets)
            for key in i.assets:
                if key.startswith('B'):
                    # link = i.assets[key].href.replace('https://data.lpdaac.earthdatacloud.nasa.gov/', 's3://')
                    link = i.assets[key].href

                    # print(link)
                    links.append(link)
    # print(item_collection.assets)
    return links

def get_reach_node_cords(reach_json_data):

    reach_id = reach_json_data['reach_id']
    sword_path = os.path.join(INPUT_DIR, 'sword', reach_json_data['sword'])

    all_nodes = []


    rootgrp = netCDF4.Dataset(sword_path, "r", format="NETCDF4")

    node_ids_indexes = np.where(rootgrp.groups['nodes'].variables['reach_id'][:].data.astype('U') == str(reach_id))

    if len(node_ids_indexes[0])!=0:
        for y in node_ids_indexes[0]:

            lat = str(rootgrp.groups['nodes'].variables['x'][y].data.astype('U'))
            lon = str(rootgrp.groups['nodes'].variables['y'][y].data.astype('U'))
            all_nodes.append([lat,lon])



        # all_nodes.extend(node_ids[0].tolist())

    rootgrp.close()

    print(f'Found {len(all_nodes)} nodes...')
    return all_nodes

def load_obs_data(obs_path):
    obs_data = netCDF4.Dataset(obs_path)
    return obs_data

def extract_date_range(obs_data):
    start = str(datetime.datetime.fromtimestamp(obs_data['reach']['time'][:][0]))[:10]
    end = str(datetime.datetime.fromtimestamp(obs_data['reach']['time'][:][-1]))[:10]
    return start+'/'+end, obs_data['reach']['time'][:]


def find_download_links_for_reach_tiles(reach_json_data, date_range):
    node_coords = get_reach_node_cords(reach_json_data)


    
    all_links = []

    local_date_range = '2020-01-01/2021-01-01'


    for i in node_coords:
        # change to date_range variable operationally
        links = find_hls_tiles(i, date_range=local_date_range)
        all_links.extend(links)

    return list(set(all_links))

def  hls_link_jdate_to_YYYYMMDD(link):
    jdate = os.path.basename(link).split('.')[3].split('T')[0]
    converted_date = str(datetime.datetime.strptime(jdate, '%Y%j').date())[:10]
    return converted_date



def sort_links_by_date(all_links):
    df = pd.DataFrame()
    df['links'] = all_links

    df['dates'] = [hls_link_jdate_to_YYYYMMDD(link) for link in all_links]
    hls_dict = df.groupby('dates')['links'].apply(list).to_dict()
    return hls_dict


def main():
    """Make a jazz noise here"""

    args = get_args()

    # Get reach to run on
    # index = int(os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX"))
    index = 0

    with open(os.path.join(INPUT_DIR, args.reaches_json)) as jsonfile:
            reach_json_data = json.load(jsonfile)[index]

    reach_id = reach_json_data['reach_id']

    obs_data = load_obs_data(os.path.join(INPUT_DIR,'swot', f'{reach_id}_SWOT.nc'))

    date_range, all_dates = extract_date_range(obs_data)

    all_links =  find_download_links_for_reach_tiles(reach_json_data, date_range)

    hls_dict = sort_links_by_date(all_links)

    # pair links with swot obs +- one day
    print(hls_dict)










# --------------------------------------------------
if __name__ == '__main__':
    main()
