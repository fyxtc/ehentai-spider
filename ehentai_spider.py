# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import os
import sys
import functools
import threading
from multiprocessing import Pool
import locale
import socket
import socks # you need to install pysocks

# Configuration
SOCKS5_PROXY_HOST = '127.0.0.1'
SOCKS5_PROXY_PORT = 1080

# Set up a proxy
socks.set_default_proxy(socks.SOCKS5, SOCKS5_PROXY_HOST, SOCKS5_PROXY_PORT)
socket.socket = socks.socksocket
# print("set proxy at 127.0.0.1:1080, make sure you are running shadowsocks or other agent in port 1080 by socks5")
    
headers = {'user-agent': 'Chrome/37.0.2062.120'}

def get_url_content(url):
    res = requests.get(url,  headers = headers)
    if res.status_code != requests.codes.ok:
        # print("get url error %d %s" % res.staus_code, res_statsu)
        raise_for_status()
    return res.text

def get_url_soup(url):
    return BeautifulSoup(get_url_content(url), "html.parser")

def get_all_img(content):
    soup = BeautifulSoup(content, 'html.parser')
    imgs = [img.get('src') for img in soup.find_all('img')]
    return imgs

def get_download_url(imgs):
    p = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    for img in imgs:
        if re.match(p, img):
            return img
        elif img.find("509.gif") != -1:
            print("Error: find 509 gif, you have downloaded too many images, reached the limit set by ehentai.org, please wait after some minutes")
            return None
    return None

def save_image(url, dir_name):
    dir_name = "download" + os.sep + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    file_name = dir_name + os.sep + url[url.rfind("/")+1:]
    if os.path.exists(file_name) and os.path.getsize(file_name) > 1000: # >1KB
        print("FILE EXISTED: %s" % file_name)
    else:
        with open(file_name, "wb") as f:
            content = requests.get(url,  headers = headers).content
            f.write(content)

def download_detail_img(url):
    # print("start download: %s" % url)
    content = get_url_content(url)
    imgs = get_all_img(content)
    download_url = get_download_url(imgs)
    if(download_url):
        soup = BeautifulSoup(content, "html.parser")
        dir_name = soup.h1.text.replace("|", "")
        dir_name = re.sub(r'[|:*?\\/\n<>"]', "", dir_name) # windows filename format limit
        save_image(download_url, dir_name)
        print("image download finish: %s" % url)
    else:
        print("NOT FOUND DOWNLOAD URL: %s" % url)
        # print(imgs)
    
def get_img_detail_url(page_url):
    soup = get_url_soup(page_url)
    # TODO: torrents
    details = [detail.get("href") for detail in soup.find_all("a") if detail.get("href") and detail.get("href").find("http://g.e-hentai.org/s/") != -1 ]
    def compare(lhs, rhs):
        return int(lhs[lhs.rfind("-")+1:]) < int(rhs[rhs.rfind("-")+1:])
    # 注意这个sorted只能对list有效，我一开始使用的是set，不行，直接乱序...
    details = sorted(details, key = functools.cmp_to_key(compare))
    return details

def download_page_img(page_url):
    # print("page start download: %s", page_url)
    detail_urls = get_img_detail_url(page_url)
    # print(detail_urls)
    finish_count = 0
    # 多进程方式：python因为GIL的关系，多线程的并发其实并没有什么卵用，所以还是用多进程吧，默认pool大小就是CPU线程数，本机为2
    pool = Pool()
    pool.map(download_detail_img, detail_urls)

    # 顺序下载方式
    # for detail_url in detail_urls:
    #     download_detail_img(detail_url)
    #     finish_count = finish_count + 1
    #     if(finish_count == 2):
    #         break; # test
        # 多线程方式： 注意这里的args=(detail_url)会报错，因为这会被认为是括号而不是元组，就炸了....
        # thread = threading.Thread(target=download_detail_img, name="download thread", args=(detail_url, ))
        # thread.start()

    # print("page finish download: %s -> count" % page_url, finish_count)

def get_all_page_url(index_url):
    soup = get_url_soup(index_url)
    pages_list = [page.get("href") for page in soup.find_all("a") if page.get("href") and page.get("href").find("http://g.e-hentai.org/g/") != -1] 
    # use set to avoid duplicate
    pages = sorted(set(pages_list))
    return pages

def download_all_page_img(index_url):
    print(">>>>>>>>>>>>>>>>>>>>>  START DOWNLOAD >>>>>>>>>>>>>>>>>>>>> %s" % index_url)
    pages = get_all_page_url(index_url)
    for page in pages:
        download_page_img(page)
    print(">>>>>>>>>>>>>>>>>>>>>  FINISH DOWNLOAD >>>>>>>>>>>>>>>>>>>>> %s" % index_url)

if __name__ == '__main__':
    if(len(sys.argv) < 2):
        print("Usage: python ehentai-spider.py url1 url2 ...")
    else:
        urls = sys.argv[1:]
        for url in urls:
            download_all_page_img(url)
        # print(get_url_soup(urls[0]), )
