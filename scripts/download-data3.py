#!/usr/bin/env python
# coding: utf-8

# # Download Data
# 
# Download all data provided by the organizers.
# There are multiple data repositories, according to a nomenclature defined here https://github.com/ecmwf-lab/climetlab-s2s-ai-challenge.
# 
# 

# In[1]:


import bs4
import multiprocessing
import os
import pathlib
import random
import requests
import urllib

from tqdm.notebook import tqdm

INDEX_TRAIN_INPUT = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/training-input/0.3.0/netcdf/index.html'
INDEX_TRAIN_OUTPUT = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/training-output-benchmark/index.html'
#INDEX_TRAIN_REFERENCE = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/training-output-reference/index.html'

INDEX_TEST_INPUT = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/test-input/0.3.0/netcdf/index.html'
INDEX_TEST_OUTPUT = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/test-output-benchmark/index.html'
#INDEX_TEST_REFERENCE = 'https://storage.ecmwf.europeanweather.cloud/s2s-ai-challenge/data/test-output-reference/index.html'
#HOME = "C:\\Users\\klow55\\github\\crims2s"
#HOME = "C:\\Users\\kahch\\src\\crims2s\\crims2s"
HOME="D:\\weatherdata"
TARGET_DIR = os.path.join(HOME, 's2s')
#os.makedirs(TARGET_DIR)


# In[2]:


def read_index(index_url):
    html = requests.get(index_url).text
    soup = bs4.BeautifulSoup(html, 'html.parser')
    try:
        table = soup.find_all('tbody')[0]
        links = table.find_all('a')
        dataset_files = [a_tag.attrs['href'] for a_tag in links]
    except Exception as e:
        print(f"{e}: {index_url}")
        dataset_files = []
    return dataset_files


# In[3]:

# In[3]:


def download_one_dataset_file(file_url):
    """Inspired by https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests."""
    url_path = urllib.parse.urlparse(file_url).path
    paths = url_path.split('/')
    download_dir = os.path.join(TARGET_DIR, paths[3])
    download_path = os.path.join(download_dir, paths[-1])
    os.makedirs(download_dir, exist_ok=True)

    with requests.get(file_url, stream=True) as stream:
        if os.path.isfile(download_path):
            """Ignore file if it already exists and file size is ok."""
            stream_len = int(stream.headers['Content-length'])
            local_len = os.path.getsize(download_path)

            if stream_len == local_len:               
                return download_path
        
        
        with open(download_path, 'wb') as f:
            for chunk in stream.iter_content(chunk_size=8192):
                f.write(chunk)
                
    return download_path


# ## Test local file

# In[ ]:


with open("D:\\weatherdata\\s2sdatafiles.txt") as fin:
    for i, line in enumerate(fin):
        if i % 4 != 3 or i<=1103:
            continue
        downloaded = download_one_dataset_file(line.strip())
        print(f"{i}:{downloaded}")


# In[ ]:
