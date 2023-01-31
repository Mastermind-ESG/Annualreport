import re
import time

import pandas as pd
import requests



headers = {"Accept": '*/*',
           'Accept-Encoding': 'gzip, deflate',
           'Accept-Language': 'zh-CN,zh;q=0.9',
           'Content-Length': "203",
           'Host': 'www.cninfo.com.cn',
           'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
           'Origin': 'http://www.cninfo.com.cn',
           'Proxy-Connection': 'keep-alive',
           'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&lastPage=index',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
           'X-Requested-With': 'XMLHttpRequest'
           }
def get_stocklist(url):
    stockdict={}
    r=requests.get(url, headers)
    stockinfo=r.json()['stockList']
    for stock in stockinfo:
        stockdict[stock['code']] = stock['orgId']
    return stockdict

def get_pdf_file(code,startdate, enddate):
    url = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
    pdfinfos = []
    if code=='':
        stock=''
    else:
        stock=code+','+stockdict[code]
    data = {'pageNum': 1,
            'pageSize': 30,
            'column': 'szse',
            'tabName': "fulltext",
            'plate': '',
            "stock": stock,
            'searchkey': '',
            'secid': '',
            'category': 'category_ndbg_szsh;category_bndbg_szsh',
            'trade': '',
            'seDate': f'{startdate}~{enddate}',
            'sortName': '',
            'sortType': '',
            'isHLtitle': 'true'
            }
    r = requests.post(url, data=data, headers=headers)
    hasMore = r.json()['hasMore']
    pagenum = 1
    while hasMore:
        data = {'pageNum': pagenum,
                'pageSize': 30,
                'column': 'szse',
                'tabName': "fulltext",
                'plate': '',
                "stock": stock,
                'searchkey': '',
                'secid': '',
                'category': 'category_ndbg_szsh;category_bndbg_szsh',
                'trade': '',
                'seDate': f'{startdate}~{enddate}',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true'
                }
        s = requests.session()
        s.keep_alive = False
        r = requests.post(url, data=data, headers=headers)
        result = r.json()['announcements']
        hasMore= r.json()['hasMore']
        for i in result:
            if re.search('摘要', i['announcementTitle']):
                pass
            elif re.search('取消', i['announcementTitle']):
                pass
            elif re.search("说明", i['announcementTitle']):
                pass
            elif re.findall('\d+', i['announcementTitle'])==[]:
                pass
            elif int(re.findall('\d+', i['announcementTitle'])[0]) not in range(2010, 2023):
                pass
            else:
                title = i['announcementTitle']
                title = title.replace('*', "")
                secName = i['secName']
                secName = secName.replace('*', '')
                secCode = i['secCode']
                adjunctUrl = i['adjunctUrl']
                rep_time = adjunctUrl[10:20]
                down_url = 'http://static.cninfo.com.cn/' + adjunctUrl
                pdfinfo = [secCode, secName, rep_time, title, down_url]
                pdfinfos.append(pdfinfo)
                print(f'{secCode}-{secName}-{title}读取成功')
                time.sleep(0.1)
                requests.DEFAULT_RETRIES = 5
        pagenum+=1
    pdfinfos = pd.DataFrame(pdfinfos)
    return pdfinfos


if __name__ == '__main__':
    stock_json_url = 'http://www.cninfo.com.cn/new/data/szse_stock.json'
    stockdict = get_stocklist(stock_json_url)
    stocklist=sorted(list(stockdict.keys()),reverse=False)
    data = get_pdf_file(stocklist[0],'2010-04-01', '2023-01-29')
    for secCode in stocklist[1:]:
        pdfinfo=get_pdf_file(secCode,'2010-04-01', '2023-01-29')
        data=pd.concat([data,pdfinfo],axis=0)

    data.columns = ['股票代码', '股票简称', '公告时间', '公告标题', 'url']
    data.to_excel('深沪京年报.xlsx', index=False)


