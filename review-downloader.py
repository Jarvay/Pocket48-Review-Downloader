#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gettext import find
import requests
import os
import json
import downloader
import time
from tqdm import tqdm
import shutil

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
        self.count = 1
        self.task_id_set = set()
        self.finish_id_set = set()

    def get_time(self, timestamp):
        time_array = time.localtime(timestamp)
        return time.strftime("%Y%m%d-%H%M%S", time_array)

    def print_menu(self):
        for key in menu_options.keys():
            print(key + '.', menu_options[key])
        option = input('请输入选项后按回车[1]:') or '1'
        self.action(option)

    def updateMembers(self):
        print('正在更新成员信息...')
        response = requests.post(
            'https://pocketapi.48.cn/user/api/v1/client/update/group_team_star',
            json={},
            headers={'Content-Type': 'application/json'})
        information = open(infomation_file_name, 'w+')
        information.write(json.dumps(response.json()['content']))

    def get_member_reviews(self, member, next='0'):
        response = requests.post('https://pocketapi.48.cn/live/api/v1/live/getLiveList', json={
            'next': next,
            'userId': member['userId'],
            'loadMore': True,
            'record': True
        })
        content = response.json()['content']
        new_next = content['next']
        reviews = content['liveList']
        for review in reviews:
            if len(self.task_id_set) < self.count or self.count == 0:
                self.get_review(review['liveId'], member)
                self.task_id_set.add(review['liveId'])
            else:
                break

        if new_next == next:
            print('下载完成')
            self.print_menu()
            return

        if len(self.task_id_set) < self.count or self.count == 0:
            self.get_member_reviews(member, new_next)

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

        index = input('请输入序号(输入b返回)[1]：') or '1'
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
        self.count = int(input('请输入下载的最近回放个数(输入0下载全部)[1]:') or 1)

        print('开始下载...')
        self.get_member_reviews(member)

    def download_member_review(self):
        member_name = input('请输入成员的名字或名字首字母(输入b返回):')
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
        response = requests.get(url, stream=True)  # (1)
        file_size = int(response.headers['content-length'])  # (2)
        if os.path.exists(dst):
            first_byte = os.path.getsize(dst)  # (3)
        else:
            first_byte = 0
        if first_byte >= file_size:  # (4)
            return file_size

        header = {"Range": f"bytes={first_byte}-{file_size}"}

        pbar = tqdm(total=file_size, initial=first_byte,
                    unit='B', unit_scale=True, desc=dst)
        req = requests.get(url, headers=header, stream=True)  # (5)
        with open(dst, 'ab') as f:
            for chunk in req.iter_content(chunk_size=1024):     # (6)
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

    def start(self):
        if not os.path.exists(downloads_dir):
            os.mkdir(downloads_dir)
        if not os.path.exists(infomation_file_name):
            self.updateMembers()
            self.print_menu()
        else:
            self.print_menu()


ReviewDownloader().start()
