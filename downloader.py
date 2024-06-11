import json
import os
import urllib3
from traceback import print_exc
from pathlib import Path
from urllib import parse
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm import tqdm
from faker import Faker

urllib3.disable_warnings()


class Downloader():
    def __init__(self, url, dst=None, filename=None, save_as_mp3=False):
        """
        :param url: m3u8 文件下载地址
        :param dst: 指定下载视频文件输出目录，不指定则为当前目录
        :param filename: 下载视频文件名
        """
        self.url = url
        self.dst = dst or os.getcwd()
        self.filename = filename or 'output.mp4'

        # ts 文件缓存目录
        self.tmp_folder = 'temp'

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SNH48 ENGINE'})
        self.session.headers.update({'HOST': 'cychengyuan-vod.48.cn'})
        self.session.verify = False

        self.proxies = {}

        config = json.loads(open('config.json').read())
        self.max_workers = config['max_workers']
        self.ffmpeg = config['ffmpeg']
        self.save_as_mp3 = save_as_mp3

    def parse_m3u8_url(self):
        """
        获取m3u8文件 并解析文件获取ts视频文件地址
        :return: ts文件下载地址
        """
        text = self.session.get(self.url).text

        return [parse.urljoin(self.url, row.strip()) for row in text.split('\n') if not row.startswith('#')]

    def check_save_folder(self):
        """
        检测视频输出目录是否正确，并创建temp目录用于临时存储ts文件
        :return: ts文件保存目录 (Path对象)
        """
        dst_folder = Path(self.dst)
        if not dst_folder.is_dir():
            raise Exception(f'{self.dst} is not a dir!')

        # 如果temp目录不存在便创建
        save_folder = Path(self.tmp_folder)
        if not save_folder.exists():
            save_folder.mkdir()

        return save_folder

    def download(self, ts_url, save_folder, pbar):
        """
        根据ts文件地址下载视频文件并保存到指定目录
        * 当前处理递归下载！！！
        :param ts_url: ts文件下载地址
        :param save_folder: ts文件保存目录
        :return: ts文件保存路径
        """
        try:
            # ts_url 可能有参数
            filename = parse.urlparse(ts_url).path.split('/')[-1]

            filepath = save_folder / filename
            if filepath.exists():
                # 文件已存在 跳过
                pbar.update(1)
                return str(filepath)

            res = self.session.get(ts_url)

            if not (200 <= res.status_code < 400):
                print(f'{ts_url}, status_code: {res.status_code}')
                raise Exception('Bad request!')

            with filepath.open('wb') as fp:
                fp.write(res.content)

        except Exception as e:
            print_exc(e)
            return self.download(ts_url, save_folder, pbar)

        pbar.update(1)
        return str(filepath)

    def merge(self, ts_file_paths):
        """
        ts文件合成
        ffmpeg -i "concat:file01.ts|file02.ts|file03.ts" -acodec copy -vcodec copy output.mp4
        ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
        :return:
        """
        filenames = [os.path.split(row)[-1] for row in sorted(ts_file_paths)]
        txt_content = '\n'.join(
            [f'file {row}' for row in filenames if row.endswith('.ts')])

        txt_filename = filenames[0].replace('.ts', '.txt')
        txt_filepath = Path(self.tmp_folder) / txt_filename
        with txt_filepath.open('w+') as fp:
            fp.write(txt_content)

        # 拼接ts文件
        command = f'{self.ffmpeg} -f concat -safe 0 -i {self.tmp_folder}/{txt_filename} -c copy {self.dst}/{self.filename}.mp4'
        os.system(command)
        if self.save_as_mp3:
            os.system(f'{self.ffmpeg} -i {self.dst}/{self.filename}.mp4 -f mp3 {self.dst}/{self.filename}.mp3')
            os.remove(Path(self.dst) / f'{self.filename}.mp4')

        # 删除txt文件
        if txt_filepath.exists():
            os.remove(txt_filepath)

    @staticmethod
    def remove_ts_file(ts_file_paths):
        for row in ts_file_paths:
            try:
                if os.path.exists(row):
                    os.remove(row)
            except Exception as e:
                print_exc(e)

    def run(self):
        """
        任务主函数
        :param max_workers: 线程池最大线程数
        """
        # 获取ts文件地址列表
        ts_urls = self.parse_m3u8_url()

        # 初始化进度条
        pbar = tqdm(total=len(ts_urls), initial=0, unit=' file',
                    unit_scale=True, desc=self.filename, unit_divisor=1)

        # 获取ts文件保存目录
        save_folder = self.check_save_folder()

        # 创建线程池，将ts文件下载任务推入线程池
        pool = ThreadPoolExecutor(max_workers=self.max_workers)
        ret = [pool.submit(self.download, url, save_folder, pbar)
               for url in ts_urls]
        ts_file_paths = [task.result() for task in ret]

        # 关闭进度条
        pbar.close()

        # 合并ts文件
        self.merge(ts_file_paths)

        # 删除ts文件
        self.remove_ts_file(ts_file_paths)
