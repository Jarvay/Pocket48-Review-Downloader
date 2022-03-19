#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Value
import requests
import os
import json
import downloader
import time
from tqdm import tqdm
import shutil
from InquirerPy import prompt, inquirer
from InquirerPy.base.control import Choice
from pprint import pprint
import sys

sys.path.append(os.path.realpath("."))

infomation_file_name = 'infomation.json'

ACTION_DOWNLOAD = '1'
ACTION_UPDATE = '2'
ACTION_CLEAR = '3'
ACTION_EXIT = '4'

menu_options = {
    ACTION_DOWNLOAD: '下载成员回放',
    ACTION_UPDATE: '更新成员信息',
    ACTION_CLEAR: '清空下载目录',
    ACTION_EXIT: '退出'
}

downloads_dir = 'downloads'


class ReviewDownloader():
    def __init__(self) -> None:
        self.page_count = 0
        self.task_id_set = []
        self.fetched_page = 0

        config = json.loads(open('config.json').read())
        self.chunk_size = config['page_size']
        self.default_checked = config['default_checked']

    def get_time(self, timestamp, format='%Y%m%d-%H%M%S'):
        time_array = time.localtime(timestamp)
        return time.strftime(format, time_array)

    def get_review_option_name(self, review):
        return f'{review["title"]}-{self.get_time(int(review["ctime"]) / 1000, "%Y-%m-%d %H:%M:%S")}'

    def print_menu(self):
        option = inquirer.select(message='请选择', choices=[
            Choice(value=ACTION_DOWNLOAD, name='1.下载成员回放'),
            Choice(value=ACTION_UPDATE, name='2.更新成员信息'),
            Choice(value=ACTION_CLEAR, name='3.清空下载目录'),
            Choice(value=ACTION_EXIT, name='Exit'),
        ]).execute()
        self.action(option)

    def updateMembers(self):
        print('正在更新成员信息...')
        response = requests.post(
            'https://pocketapi.48.cn/user/api/v1/client/update/group_team_star',
            json={},
            headers={'Content-Type': 'application/json'})
        information = open(infomation_file_name, 'w+')
        information.write(json.dumps(response.json()['content']))

    def get_member_reviews(self, member, review_list=[], next='0'):
        response = requests.post('https://pocketapi.48.cn/live/api/v1/live/getLiveList', json={
            'next': next,
            'userId': member['userId'],
            'loadMore': True,
            'record': True
        })
        content = response.json()['content']
        new_next = content['next']
        reviews = content['liveList']

        review_list.extend(reviews)

        self.fetched_page += 1

        if new_next == next or self.fetched_page == self.page_count:
            print(f'拉取完毕，共{len(review_list)}个回放')

            download_all = inquirer.text('是否下载全部拉取到的回放(Y/n)：').execute() or 'y'
            # 下载全部
            if download_all == 'y':
                for review in review_list:
                    self.task_id_set.append(review['liveId'])
            # 选择下载
            else:
                chunks = self.chunker(review_list, self.chunk_size)
                nameIds = {}
                for index, chunk in enumerate(chunks):
                    items = []
                    for k, v in enumerate(chunk):
                        item = Choice(value=v['liveId'], name=self.get_review_option_name(v), enabled=self.default_checked)
                        items.append(item)

                    result = inquirer.checkbox(
                        message=f'第{str(index + 1)}页', choices=items).execute()
                    for live_id in result:
                        self.task_id_set.append(live_id)

            print('开始下载')
            for id in self.task_id_set:
                self.get_review(id, member)
            return

        if self.fetched_page < self.page_count or self.page_count == 0:
            self.get_member_reviews(member, review_list, new_next)

    def get_review(self, id, member):
        response = requests.post(
            'https://pocketapi.48.cn/live/api/v1/live/getLiveOne', json={
                'liveId': id
            })
        review = response.json()['content']
        dir = downloads_dir + '//' + member['realName']
        if not os.path.exists(dir):
            os.mkdir(dir)
        print('开始下载：', review['title'])
        file_name: str = member['realName'] + '-' + \
            self.get_time(int(review['ctime']) / 1000) + '.mp4'

        dst = dir + '//' + file_name
        playStreamPath = review['playStreamPath']
        if not os.path.exists(dst):
            if playStreamPath.endswith('.m3u8'):
                downloader.Downloader(playStreamPath, dir,
                                      file_name).run()
            else:
                self.download_mp4(playStreamPath, dst)

        else:
            print('已下载，跳过')

    def select_member(self, filter_members):
        print('找到以下成员：')
        for index, member in enumerate(filter_members):
            print(str(index + 1) + '.', member['groupName'] + '-' + member['realName'],
                  'ID-' + str(member['userId']))

        index = inquirer.text('请输入序号(输入[b]返回)[1]：', default='1').execute() or '1'
        if (index == 'b'):
            self.download_member_review()
            return

        if not index.isdigit():
            self.select_member(filter_members)
            return

        if int(index) > len(filter_members):
            print()
            print('超出范围，请重新输入')
            print()
            self.select_member(filter_members)

        member = filter_members[int(index) - 1]

        self.page_count = int(inquirer.number('请输入拉取的页数(默认拉取全部)[0]:', default=0).execute() or 0)

        self.reviews_file_name = downloads_dir + '//' + \
            f'{member["realName"]}-{member["userId"]}.json'

        print('开始拉取成员回放列表...')
        self.get_member_reviews(member)

    def download_member_review(self):
        member_name = inquirer.text(message='请输入成员的名字或名字首字母', instruction='(输入[b]返回):').execute()
        if member_name == 'b':
            self.print_menu()
            return

        file = open(infomation_file_name)
        members = list(json.loads(file.read())['starInfo'])
        filter_members = list(filter(
            lambda member: member['realName'].find(member_name) != -1
            or member['abbr'].find(member_name) != -1, members))
        if len(filter_members) == 0:
            print('没有找到符合条件的成员')
            self.download_member_review()
            return
        self.select_member(filter_members)

    def action(self, option):
        if option == ACTION_DOWNLOAD:
            self.download_member_review()
        elif option == ACTION_UPDATE:
            self.updateMembers()
            self.print_menu()
        elif option == ACTION_EXIT:
            print('退出')
        elif option == ACTION_CLEAR:
            self.clear()
            self.print_menu()
        else:
            self.print_menu()

    def download_mp4(self, url, dst):
        response = requests.get(url, stream=True)
        file_size = int(response.headers['content-length'])
        if os.path.exists(dst):
            first_byte = os.path.getsize(dst)
        else:
            first_byte = 0
        if first_byte >= file_size:
            return file_size

        header = {"Range": f"bytes={first_byte}-{file_size}"}

        pbar = tqdm(total=file_size, initial=first_byte,
                    unit='B', unit_scale=True, desc=dst)
        req = requests.get(url, headers=header, stream=True)
        with open(dst, 'ab') as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
        pbar.close()
        return file_size

    def clear(self):
        shutil.rmtree(downloads_dir)
        os.mkdir(downloads_dir)
        print()
        print('已清空')
        print()

    def chunker(self, iter, size):
        chunks = []
        if size < 1:
            raise ValueError('Chunk size must be greater than 0.')
        for i in range(0, len(iter), size):
            chunks.append(iter[i:(i+size)])
        return chunks

    def start(self):
        if not os.path.exists(downloads_dir):
            os.mkdir(downloads_dir)
        if not os.path.exists(infomation_file_name):
            self.updateMembers()
            self.print_menu()
        else:
            self.print_menu()


ReviewDownloader().start()
