"""
判断迅雷文件是否下载完成，下载完成后转移到指定文件夹

"""

import os
import requests
import shutil
import urllib
import base64
import json
import time
import hmac
import hashlib
import datetime


def get_task_list(this_path: str) -> list:
    """

    :param this_path: 迅雷下载文件夹
    :return: 任务列表
    根目录下一个文件认为是一个任务，一个文件夹认为是一个目录。。。
    """
    this_result = list()
    for this_path_i in os.listdir(this_path):
        this_path_i = os.path.join(this_path, this_path_i)
        this_result.append(this_path_i)

    return this_result


def get_is_download(this_path: str) -> bool:
    """

    :param this_path: 任务路径
    :return: 返回下载状态
    判断任务是否下载完毕
    """

    # 如果是单文件
    if os.path.isfile(this_path):
        # 判断后缀名
        if this_path.endswith('.xltd'):
            return False
        else:
            return True

    # 递归检查文件状态
    for root, dirs, files in os.walk(this_path):
        for file in files:
            if file.endswith('.xltd'):
                return False

    return True


def get_path_size(this_path):
    # 判断是否为文件
    if os.path.isfile(this_path):
        size = os.path.getsize(this_path)
    # 判断是否为文件夹
    elif os.path.isdir(this_path):
        size = 0
        for dir_path, dir_names, file_names in os.walk(this_path):
            for filename in file_names:
                file_path = os.path.join(dir_path, filename)
                size += os.path.getsize(file_path)
    else:
        # 路径不存在或不是文件或文件夹
        size = 0
    # 将大小转换为GB单位
    return size / (1024 ** 3)


def send_msg(date_str, msg):
    """
    Sends a message via DingTalk robot.发不出去求
    """
    try:
        timestamp = str(round(time.time() * 1000))
        secret = 'secret'
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f'https://oapi.dingtalk.com/robot/send?access_token=token&timestamp={timestamp}&sign={sign}'
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        content_str = f"{date_str} 推送：\n\n{msg}\n"

        data = {
            "msgtype": "text",
            "text": {
                "content": content_str
            },
        }
        requests.post(url, data=json.dumps(data), headers=headers)
    except:
        pass


def copy_folder(source_folder: str, destination_folder: str) -> bool:
    """

    :param source_folder:
    :param destination_folder:
    :return:
    """
    this_leval = 0
    first_level_directory = ''
    if os.path.isfile(source_folder):
        # 判断目标文件夹是否存在
        if not os.path.exists(destination_folder) and is_safe(destination_folder):
            shutil.copyfile(source_folder, os.path.join(destination_folder, os.path.basename(source_folder)))
    elif os.path.isdir(source_folder):
        # 遍历文件夹
        for root, dirs, files in os.walk(source_folder):
            this_leval += 1
            # 如果是第一级，文件夹路径应该是：下载根目录/下载任务目录
            if this_leval == 1:
                first_level_directory = root
            this_dir = root.replace(first_level_directory, destination_folder)
            print(this_dir)

            if not os.path.exists(this_dir):
                # 创建多级目录
                os.makedirs(this_dir)
            for file in files:
                # 白名单过滤
                if os.path.exists(file) or not is_safe(file):
                    continue
                else:
                    shutil.copyfile(os.path.join(root, file), os.path.join(this_dir, file))
    else:
        # 其他情况
        print(1)
        return False
    return True


def is_safe(this_path: str) -> bool:
    """

    :param this_path: 要判断的路径
    :return: 是否安全
    """
    media_file_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico',
        '.mp3', '.wav', '.flac', '.aac', '.wma', '.ogg',
        '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.mpeg', '.3gp',
        '.gif', '.swf',
        '.srt', '.sub', '.ass', '.vtt', '.iso', '.txt', '.img'
    ]
    # 判断是否以白名单文件后缀结尾
    if this_path.endswith(tuple(media_file_extensions)):
        return True
    else:
        return False


def main():
    # 两个文件夹
    source_dir = 'Z:\下载'
    to_dir = 'Y:'

    # 获取任务列表
    task_list = get_task_list(source_dir)
    print(task_list)

    # 遍历列表，获取任务状态
    task_list_ed = [x for x in task_list if get_is_download(x)]

    size_ed = 0
    for task in task_list_ed:
        size_ed += get_path_size(task)

    if len(task_list_ed) > 0:
        # 发送任务开始通知
        msg = f"检测到，新的已下载务数{len(task_list_ed)}, 大小{size_ed}G"
        send_msg(datetime.datetime.now().strftime('%H:%M'), msg)

        # 开始copy
        success_list = list()
        for task_i in task_list_ed:
            if copy_folder(task_i, to_dir):
                success_list.append(task_i)
                shutil.rmtree(task_i)

        # 发送完成通知
        msg = f'任务完成{len(success_list)}， 在下载的任务数为{len(task_list) - len(task_list_ed)}'
        send_msg(datetime.datetime.now().strftime('%H:%M'), msg)


if __name__ == '__main__':
    while True:
        main()
        time.sleep(20)
        print(1)

