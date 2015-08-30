# ehentai-spider
A spider to scratch ehentai.org images by python3, also packaged in exe for Windows user

#Important Prerequisite
script will set proxy at 127.0.0.1:1080, make sure you are running shadowsocks or other agent in port 1080 by socks5

#Run by exe
The exe file is in dist folder, you can just run it by cmd

Usage: `ehentai_spider url1 url2 `

for example: `ehentai_spider.exe http://g.e-hentai.org/g/847453/8448eb8622/ http://g.e-hentai.org/g/847701/a466d45a4e/`


#Run by python
#Installation
You need some third libs: 
* requests

`pip install requests`
* beautifulsoup4

`pip install beautifulsoup4`
* pysocks, 

`pip install pysocks`    

#Usage
python ehentai-spider.py url1 url2 ...

#For Example
`python ehentai_spider.py http://g.e-hentai.org/g/847453/8448eb8622/ http://g.e-hentai.org/g/847701/a466d45a4e/`



