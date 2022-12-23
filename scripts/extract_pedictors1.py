#!/usr/bin/env python
# coding: utf-8

# In[1]:


import xarray as xr
import os
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn import metrics
import time
import xarray as xr
import cupy_xarray
import cupy as cp
#import cProfile
import threading

res = 2.8125
local_dir = f"D:\\weatherbench\\{res}deg"


# In[2]:


def get_all_4_corners():
    d = xr.open_dataset("D:\\weatherbench\\2.8125deg\\2m_temperature\\2m_temperature_2.8125deg\\2m_temperature_1979_2.8125deg.nc")
    lats = [lt.item() for lt in d['lat']]
    lons = [ln.item() for ln in d['lon']]
    output = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            if i == len(lats)-1:
                continue
            if j == len(lons)-1:
                continue
            output.append([(lat, lon), (lat, lons[j+1]), (lats[i+1], lon), (lats[i+1], lons[j+1])])
    return output


def get_daily_value_for_year(feature_info, coords, year, d):
    feature, df_fld = feature_info
    if d is None:
        d = xr.open_dataset(os.path.join(local_dir, feature, f"{feature}_{res}deg", f"{feature}_{year}_{res}deg.nc"))
        dt1 = dt2 = None
    else:
        dt1 = f"{year}-01-01T00:00:00.000000000"
        dt2 = f"{year}-12-31T23:00:00.000000000"
    quad_avg = []

    for lat, lon in coords:
#        t0 = time.time()
        if dt1 is None:
            data = d.sel(lon=lon, lat=lat).to_dataframe()[df_fld]
        else:
            data = d.sel(lon=lon, lat=lat, time=slice(dt1, dt2)).to_dataframe()[df_fld]
    #        print(f"sel {time.time()-t0}")
    # hourly temperature: each day covers 24 entries. Take the daily average over 24hrs
        one_year_daily=np.array([np.mean(data[i:i+24]) for i in range(0, len(data), 24)])
        quad_avg.append(one_year_daily[:365].reshape((1, 365)))
    return quad_avg


def linearize(x):
    linearized = np.array([])
    for chunk in x:
        linearized = np.concatenate((linearized, chunk), axis=0)
    return linearized


def detrend(feature, coords, years, d):
    """
    Extract the mean feature value for each day in a year over the period between y1 and y2 inclusive and use
    it to do seasonal detrending.
    """
    y1, y2 = years
    data = None
    t0 = time.time()
    for y in range(y1, y2+1):
        more_data = get_daily_value_for_year(feature, coords, y, d)
        #print(f"    Time needed for {y}: {time.time()-t0}")
        if data is None:
            data = more_data
        else:
            for i in range(len(data)):
                data[i] = np.concatenate((data[i], more_data[i]), axis=0)

    t1 = time.time()
#    np.savetxt(f"daily_averages{nombor}.txt", data, delimiter=',')
    # means is an array where mean[0] is the feature value average over the years between y1 and y2 on the 
    # on the first day of a year
    detrendeds = []
    means_list = []
    for dt in data:
        means = np.array([np.array([dt[i, j] for i in range(y2-y1+1)]).mean() for j in range(365)])
        detrendeds.append(dt - means)
        means_list.append(means)
    # output format: every row is a year, every year has 365 columns
    print(f"40yr:{t1-t0}")
    return detrendeds, means_list, data

def get_autummn_day_indices():
    autumn_1st_day = datetime(1979, 9, 1).timetuple().tm_yday
    autumn_last_day = datetime(1979, 11, 30).timetuple().tm_yday
    return (autumn_1st_day, autumn_last_day)

def get_winter_day_indices():
    winter_1st_day = datetime(1979, 12, 1).timetuple().tm_yday
    winter_last_day = datetime(1979, 3, 1).timetuple().tm_yday
    return (winter_1st_day, winter_last_day)

def get_summer_day_indices():
    first_day = datetime(1979, 6, 1).timetuple().tm_yday
    last_day = datetime(1979, 8, 31).timetuple().tm_yday
    return (first_day, last_day)


# In[3]:


semua = get_all_4_corners()
df = pd.read_csv("yearly_winter_anomaly_clusters.csv")
#semua = semua[:10]
#semua


# lat:40.78125, lon:284.0625, 0
# lat:40.78125, lon:286.875, 1
# lat:43.59375, lon:284.0625, 2
# lat:43.59375, lon:286.875, 3

# semua = [[(40.78125, 284.0625), (40.78125, 286.875), (43.59375, 284.0625), (43.59375, 286.875)]]

# In[4]:


#first_day, last_day = get_autummn_day_indices()
#first_day, last_day = get_winter_day_indices()

def main(semua, nombor, d):
    first_day, last_day = get_summer_day_indices()
    avgs_empat = []
    year_start = 1979
    year_end = year_start + 38
    if last_day < first_day:
        year_end += 1 # for winter data, data from one more year are needed
#result_file = "sil_t2m_sanity_score.csv"
    result_file = f"sil_t2m_summer_score_{nombor}.csv"
    with open(result_file, "a") as fout:
        fout.write("row,lat0,lon0,lat1,lon1,lat2,lon2,lat3,lon3,sil_score\n")
    print(f"Thread {nombor} starting")
    for i, one_empat in enumerate(semua):
        avgs_empat = []

        t0 = time.time()
        detrendeds, _, _ = detrend(("2m_temperature", 't2m'), one_empat, (year_start, year_end), d)
        for detrended in detrendeds:
            if last_day > first_day:
                avgs_empat.append([float(x.mean()) for x in detrended[:, first_day:last_day]])
            else:
                front_chunk = detrended[:-1, first_day:]
                back_chunk = detrended[1:, :last_day] # 2nd part of winter is in the next year
                detrended = np.concatenate((front_chunk, back_chunk), axis=1)
                avgs_empat.append([float(x.mean()) for x in detrended])

        print(f"{nombor}Time {i}: {time.time()-t0}")
#    print(avgs_empat)
        curr_score = metrics.silhouette_score(np.array(avgs_empat).T, df['cluster'])
        coords = ','.join([f"{pt[0]},{pt[1]}" for pt in one_empat])
        result = f"{i},{coords},{curr_score}\n"
        with open(result_file, "a") as fout:
            fout.write(result)
    print(f"Thread {nombor} ending")

# In[5]:
def main_try(semua, nombor, d):
    try:
        main(semua, nombor, d)
    except Exception as e:
        print(e)

#cProfile.run('main()')


# In[ ]:


#from line_profiler import LineProfiler
#profile = LineProfiler(main())
#profile.print_stats()
d = xr.open_mfdataset("D:\\weatherbench\\2.8125deg\\2m_temperature\\2m_temperature_2.8125deg\\2m_temperature_*_2.8125deg.nc")
seg_num = 2
sub_size = len(semua) // seg_num
all_threads = []
for i in range(1, seg_num):
    if i < seg_num-1:
        sub_semua = semua[i*sub_size:(i+1)*sub_size]
    else:
        sub_semua = semua[i*sub_size:]
    x = threading.Thread(target=main_try, args=(sub_semua, i, None))
    x.start()
    all_threads.append(x)

for one_thr in all_threads:
    one_thr.join()
