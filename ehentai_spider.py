# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import os
import sys
import time
import functools
import threading
from multiprocessing import Pool
import locale
import logging
import socket
import socks # you need to install pysocks

import logging  

def set_log():
    #写日志，以不同的级别。
    logging.basicConfig(filemode = "w", filename = 'log.txt',level = logging.INFO, format = '[%(asctime)s %(levelname)s] %(message)s', datefmt = '%Y%m%d %H:%M:%S')
    #定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


# Configuration
# SOCKS5_PROXY_HOST = '127.0.0.1'
# SOCKS5_PROXY_PORT = 1080

# Set up a proxy
# socks.set_default_proxy(socks.SOCKS5, SOCKS5_PROXY_HOST, SOCKS5_PROXY_PORT)
# socket.socket = socks.socksocket
# logging.info("set proxy at 127.0.0.1:1080, make sure you are running shadowsocks or other agent in port 1080 by socks5")

def set_proxy():
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
    socket.socket = socks.socksocket    

headers = {'user-agent': 'Chrome/37.0.2062.120'}

def get_url_content(url):
    res = requests.get(url,  headers = headers, timeout=10)
    if res.status_code != requests.codes.ok:
        # logging.info("get url error %d %s" % res.staus_code, res_statsu)
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
            logging.error("Error: find 509 gif, you have downloaded too many images, reached the limit set by ehentai.org, please wait after some minutes")
            return None
    return None

def save_image(url, dir_name, src_url):
    dir_name = "download" + os.sep + dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    name = ""
    if url[url.rfind("/")+1:].find("image.php") != -1:
        name = url[url.rfind("=")+1:]
        logging.info("rename file name to " + name + " in " + url)
    else:
        name = url[url.rfind("/")+1:]
    file_name = dir_name + os.sep + name

    if os.path.exists(file_name) and os.path.getsize(file_name) > 1000: # >1KB
        logging.info("FILE EXISTED: %s" % file_name)
    else:
        with open(file_name, "wb") as f:
            content = requests.get(url,  headers = headers).content
            f.write(content)
            logging.info("image download finish: %s" % src_url)

def download_detail_img(url):
    # logging.info("start download: %s" % url)
    content = get_url_content(url)
    imgs = get_all_img(content)
    download_url = get_download_url(imgs)
    if(download_url):
        soup = BeautifulSoup(content, "html.parser")
        dir_name = soup.h1.text.replace("|", "")
        dir_name = re.sub(r'[|:*?\\/\n<>"]', "", dir_name) # windows filename format limit
        save_image(download_url, dir_name, url)
    else:
        logging.error("NOT FOUND DOWNLOAD URL: %s" % url)
    
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
    # logging.info("page start download: %s", page_url)
    detail_urls = get_img_detail_url(page_url)
    # logging.info(detail_urls)
    finish_count = 0
    # 多进程方式：python因为GIL的关系，多线程的并发其实并没有什么卵用，所以还是用多进程吧，默认pool大小就是CPU线程数，本机为2
    # pool = Pool()
    # pool.map(download_detail_img, detail_urls)

    # 顺序下载方式
    for detail_url in detail_urls:
        download_detail_img(detail_url)
        finish_count = finish_count + 1

        # if(finish_count == 2):
        #     break; # test
        # 多线程方式： 注意这里的args=(detail_url)会报错，因为这会被认为是括号而不是元组，就炸了....
        # thread = threading.Thread(target=download_detail_img, name="download thread", args=(detail_url, ))
        # thread.start()

    # logging.info("page finish download: %s -> count" % page_url, finish_count)

def get_all_page_url(index_url):
    soup = get_url_soup(index_url)
    pages_list = [page.get("href") for page in soup.find_all("a") if page.get("href") and page.get("href").find("http://g.e-hentai.org/g/") != -1] 
    # use set to avoid duplicate
    pages = sorted(set(pages_list))
    return pages

def download_all_page_img(index_url):
    logging.info("START DOWNLOAD: " + index_url + " >>>>>>>>>")
    pages = get_all_page_url(index_url)
    for page in pages:
        download_page_img(page)
    logging.info("FINISH DOWNLOAD: " + index_url + " >>>>>>>>>")

def get_all_index_url(search_url):
    content = get_url_soup(search_url)
    index_urls = [index_url.get("href") for index_url in content.find_all("a") if index_url.get("href").find("http://g.e-hentai.org/g/") != -1]
    return index_urls

if __name__ == '__main__':
    if(len(sys.argv) < 2):
        print("Usage: python ehentai_spider.py url1 url2 ...")
        print("Usage: ehentai_spider.exe url1 url2 ...")
    else:
        set_log()
        url_start_index = 1
        if sys.argv[1] == "1080":
            logging.info("set shadowsocks proxy in port 127.0.0.1:1080")
            set_proxy()
            url_start_index = 2

        start_url = sys.argv[url_start_index]
        if start_url.find("http://g.e-hentai.org/?") != -1: 
            # search result url, next parm is index in this serarch page for continue download if interrupted in last time
            index_urls = get_all_index_url(start_url)
            # 解析页面参数的类型，有四种格式:
            # 不写：默认为1，从第一个开始下载到整页结束
            # 一个正数：如6，表示从第六个开始下载到整页结束，通常用于上次全页下载被突然中断，从上次中断的页面开始下载即可
            # 正数列表：如6,7,8, 使用英文逗号分割的方式，表示从整页中下载这些页面
            # 负数列表：如-6,-7,-8, 使用英文逗号分割的方式，注意只要第一个数负数即可，表示从整页中删除这些页面，其余正常下载
            # 注意一个负数的含义和负数列表一样，都是删除，但注意一个正数和正数列表是一样的，因为没必要，如果只有一个的话，直接传那个的地址就行了，用不到page的解析
            logging.debug("before index url count " + str(len(index_urls)) + "\n" + str(index_urls))
            search_parm = sys.argv[url_start_index+1] if len(sys.argv) > url_start_index+1 else 1
            print("search_parm: " + str(search_parm))
            if search_parm != 1:
                page_list = search_parm.split(",")
                if len(page_list) == 1:
                    if(int(page_list[0]) > 0):
                        # 第五个是从索引为4开始切
                        index_urls = index_urls[int(search_parm) - 1:] 
                    else:
                        index_urls.remove(index_urls[int(search_parm)-1])
                else:
                    if int(page_list[0]) > 0:
                        index_urls = [index_urls[i] for i in range(len(index_urls)) if str(i+1) in page_list ]
                    else:
                        index_urls = [index_urls[i] for i in range(len(index_urls)) if str(-(i+1)) not in page_list ]



            logging.info(" index url count " + str(len(index_urls)) + "\n" + str(index_urls))
            # for index_url in index_urls:
            #     download_all_page_img(index_url)

        else:
            urls = sys.argv[url_start_index:]
            for url in urls:
                download_all_page_img(url)

        logging.info("FINISH ALL DOWNLOAD JOB !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

