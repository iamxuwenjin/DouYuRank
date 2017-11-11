# coding=utf-8
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import threading
import jsonpath
import requests
import Queue
import json
import csv
import re



class DouYuRank(object):
    def __init__(self):
        self.base_url = "https://www.douyu.com/"
        self.first_url = "https://www.douyu.com/directory/rank_list/game"
        self.headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"}
        # 创建url队列
        self.url_queue = Queue.Queue()
        #创建html队列
        self.html_queue = Queue.Queue()
        self.pattern = re.compile(r"(=)(.*?)(;)")
        self.anchors_info = []
        self.richs_info = []


    def load_page(self,url):
        html = requests.get(url=url, headers=self.headers).content
        self.html_queue.put(html)

    def parse_url(self, html):
        soup = BeautifulSoup(html,"lxml")
        li_list = soup.select(".rank-catagory li")
        for a in li_list:
            url = a.select("a")[0].get("href")
            class_name = a.select("a")[0].get("title")
            self.url_queue.put(url)

    def get_rank(self, title, rank_data, query):
        day_list = rank_data['anchorListData'][query]
        for anchor in day_list:
            room_id = anchor['room_id']
            nick_name = anchor['nickname']
            rank = anchor['id']
            anchor_info = [rank,nick_name,room_id,title,query[0:-8]]
            self.anchors_info.append(anchor_info)
            # print anchor_info
        # print self.anchors_info
        self.write_anchor(anchor=self.anchors_info)

    def get_rich(self, title, rank_data, query):
        day_list = rank_data['userListData'][query]
        rich_info = []
        for rich in day_list:
            gx = rich['gx']
            nick_name = rich['nickname']
            level = rich['level']
            rank = rich['id']
            rich_info = [rank,nick_name,gx,level,title,query[0:-8]]
            self.richs_info.append(rich_info)
        self.write_richman(rich=self.richs_info)

    def parse_page(self,html):
        soup = BeautifulSoup(html,'lxml')
        title = soup.select('title')[0].get_text()
        anchors = soup.select('script')
        rank_list_info = anchors[7]
        rank_list_info = str(rank_list_info)
        rank_data = self.pattern.search(rank_list_info).group(2)
        rank_data = json.loads(rank_data)
        # 得到主播周榜列表
        day = 'dayListData'
        self.get_rank(title=title, rank_data=rank_data, query=day)

        self.get_rich(title=title, rank_data=rank_data, query=day)

        # 得到主播周榜列表
        week = 'weekListData'
        self.get_rank(title=title,rank_data=rank_data,query=week)
        self.get_rich(title=title,rank_data=rank_data,query=week)
        # 得到主播月榜列表
        month = 'monthListData'
        self.get_rank(title=title, rank_data=rank_data, query=month)
        self.get_rich(title=title, rank_data=rank_data, query=month)


    def write_anchor(self, anchor):
        # with open('anchor_info.txt','ab') as f:
        #     f.write(anchor)
        #     f.write('\n')
        # print anchor
        csv_file = file("anchor.csv", "w")
        # 创建csv文件的读写对象
        csv_wirter = csv.writer(csv_file)
        # 构建表头
        sheet_data = ['排名','主播','房间号','分区','榜单类别']
        csv_wirter.writerow(sheet_data)
        # writerows 写入多行数据，参数是一个嵌套列表
        csv_wirter.writerows(anchor)
        csv_file.close()


    def write_richman(self,rich):
        csv_file = file("richman.csv", "w")
        # 创建csv文件的读写对象
        csv_wirter = csv.writer(csv_file)
        # 构建表头
        sheet_data = ['排名', 'id', '贡献', '等级','分区', '榜单类别']
        csv_wirter.writerow(sheet_data)
        # writerows 写入多行数据，参数是一个嵌套列表
        csv_wirter.writerows(rich)
        csv_file.close()

    def start_work(self):
        thread_list = []
        self.load_page(url=self.first_url)
        index_html = self.html_queue.get()
        self.parse_url(index_html)
        while not self.url_queue.empty():
            url = self.url_queue.get()
            url = self.base_url+url
            thread = threading.Thread(target=self.load_page,args=(url,))
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()
        while not self.html_queue.empty():
            html = self.html_queue.get()
            self.parse_page(html)

if __name__ == '__main__':
    rank= DouYuRank()
    rank.start_work()