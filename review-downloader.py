#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import requests
import shutil
import sys
import time
from InquirerPy import prompt, inquirer
from InquirerPy.base.control import Choice
import enum
from tqdm import tqdm

import downloader

sys.path.append(os.path.realpath("."))

information_file_name = 'information.json'

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

headers = {
    'host': 'cychengyuan-vod.48.cn'
}


class LiveType(enum.Enum):
    Video = 1
    Radio = 2


class ReviewDownloader():
    def __init__(self) -> None:
        self.reviews_file_name = None
        self.page_count = 0
        self.task_id_set = []
        self.fetched_page = 0

        config = json.loads(open('config.json').read())
        self.chunk_size = config['page_size']
        self.default_checked = config['default_checked']
        self.max_retry_count = config['max_retry_count']
        self.always_mp4 = config['always_mp4']

    @staticmethod
    def get_time(timestamp, format='%Y%m%d-%H%M%S'):
        time_array = time.localtime(timestamp)
        return time.strftime(format, time_array)

    def get_review_option_name(self, review):
        live_type = '电台' if review['liveType'] == LiveType.Radio.value else '直播'
        return f'{live_type} {review["title"]}-{self.get_time(int(review["ctime"]) / 1000, "%Y-%m-%d %H:%M:%S")}'

    def print_menu(self):
        option = inquirer.select(message='请选择', choices=[
            Choice(value=ACTION_DOWNLOAD, name='1.下载成员回放'),
            Choice(value=ACTION_UPDATE, name='2.更新成员信息'),
            Choice(value=ACTION_CLEAR, name='3.清空下载目录'),
            Choice(value=ACTION_EXIT, name='Exit'),
        ]).execute()
        self.action(option)

    @staticmethod
    def update_members():
        print('正在更新成员信息...')
        response = requests.post(
            'https://pocketapi.48.cn/user/api/v1/client/update/group_team_star',
            json={},
            headers={'Content-Type': 'application/json'})
        information = open(information_file_name, 'w+')
        information.write(json.dumps(response.json()['content']))

    def get_member_reviews(self, member, next_page='0'):
        response = requests.post('https://pocketapi.48.cn/live/api/v1/live/getLiveList', json={
            'next': next_page,
            'userId': member['userId'],
            'loadMore': True,
            'record': True
        })
        self.fetched_page += 1
        content = response.json()['content']
        new_next = content['next']
        reviews = list(filter(lambda r: str(r['userInfo']['userId']) == str(member['userId']), content['liveList']))

        if len(reviews) == 0:
            self.get_member_reviews(member, new_next)
            return

        items = []
        for review in reviews:
            item = Choice(value=review['liveId'], name=self.get_review_option_name(review),
                          enabled=self.default_checked)
            items.append(item)

        result = inquirer.checkbox(
            message=f'第{str(self.fetched_page)}页', choices=items).execute()
        print('result', result)

        for live_id in result:
            self.task_id_set.append(live_id)

        go_on = inquirer.text('是否继续选择下一页(Y/n)：').execute() or 'y'
        if go_on == 'y':
            self.get_member_reviews(member, new_next)
        else:
            print(f'选择完毕，开始下载')
            for id in self.task_id_set:
                self.get_review(id, member)

        if new_next == next_page:
            print(f'选择完毕，开始下载')
            for id in self.task_id_set:
                self.get_review(id, member)

    def download_review(self, stream_path, member_dir, file_name, retry_count=0, save_as_mp3=False):
        dst = member_dir + '//' + file_name
        if not os.path.exists(dst):
            try:
                if stream_path.endswith('.m3u8'):
                    downloader.Downloader(stream_path, member_dir,
                                          file_name, save_as_mp3).run()
                else:
                    self.download_mp4(stream_path, dst)
            except:
                if retry_count < self.max_retry_count:
                    print('下载失败，重试')
                    self.download_review(stream_path, member_dir, file_name, retry_count + 1, save_as_mp3)
                else:
                    print('重试次数超过预设值，跳过')

        else:
            print('已下载，跳过')

    def get_review(self, id, member):
        response = requests.post(
            'https://pocketapi.48.cn/live/api/v1/live/getLiveOne', json={
                'liveId': id
            })
        review = response.json()['content']
        member_dir = downloads_dir + '//' + member['realName']
        if not os.path.exists(member_dir):
            os.mkdir(member_dir)
        print('开始下载：', review['title'])

        file_name: str = member['realName'] + '-' + self.get_time(int(review['ctime']) / 1000)

        play_stream_path = review['playStreamPath']
        save_as_mp3 = (self.always_mp4 is False) and review['liveType'] == LiveType.Radio.value
        self.download_review(play_stream_path, member_dir, file_name, save_as_mp3=save_as_mp3)

    def select_member(self, filter_members):
        print('找到以下成员：')
        for index, member in enumerate(filter_members):
            print(str(index + 1) + '.', member['groupName'] + '-' + member['realName'],
                  'ID-' + str(member['userId']))

        index = inquirer.text('请输入序号(输入[b]返回)[1]：', default='1').execute() or '1'
        if index == 'b':
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

        self.reviews_file_name = downloads_dir + '//' + \
                                 f'{member["realName"]}-{member["userId"]}.json'

        print('开始拉取成员回放列表...')
        self.get_member_reviews(member)

    def download_member_review(self):
        member_name = inquirer.text(message='请输入成员的名字或名字首字母', instruction='(输入[b]返回):').execute()
        if member_name == 'b':
            self.print_menu()
            return

        file = open(information_file_name)
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
            self.update_members()
            self.print_menu()
        elif option == ACTION_EXIT:
            print('退出')
        elif option == ACTION_CLEAR:
            self.clear()
            self.print_menu()
        else:
            self.print_menu()

    @staticmethod
    def download_mp4(url, dst):
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

    @staticmethod
    def chunker(iter, size):
        chunks = []
        if size < 1:
            raise ValueError('Chunk size must be greater than 0.')
        for i in range(0, len(iter), size):
            chunks.append(iter[i:(i + size)])
        return chunks

    def start(self):
        if not os.path.exists(downloads_dir):
            os.mkdir(downloads_dir)
        if not os.path.exists(information_file_name):
            self.update_members()
            self.print_menu()
        else:
            self.print_menu()


ReviewDownloader().start()
