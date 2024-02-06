# 口袋48成员回放下载器

## 使用方法
### Mac或Linux
1. 安装`python`及`ffmpeg`
2. 运行`pip install -r requirements.txt`
3. 运行`python review-downloader.py`

### Windows
[下载压缩包](https://wwa.lanzoui.com/b00n47cgd)解压后运行.exe文件

### 配置文件说明
```json5 lines
{
  "max_workers": 10, // 同时下载线程数
  "ffmpeg": "ffmpeg", // ffmpeg路径
  "page_size": 20, // 这个是选择要下载的回放时的分页大小
  "default_checked": true, // 选择指定回放时是否默认选中
  "max_retry_count": 3 // 下载失败时的最大重试次数
}

```

## 其他
- m3u8下载功能复制了[https://www.jianshu.com/p/a8d8195c7ade](https://www.jianshu.com/p/a8d8195c7ade)的代码
