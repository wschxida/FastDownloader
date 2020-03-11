import asyncio
import aiohttp
import time
import configparser
import logging
import random
import sys
import datetime
import os
import json
from async_timeout import timeout

log = logging.getLogger(__name__)


async def get_response(session, url, proxy_info):
    """
    传入session、url、proxy_info, 发送get请求，返回response的text
    :param session:
    :param url:
    :param proxy_info:
    :return: response.text()
    """
    with timeout(60):
        async with session.get(url, proxy=proxy_info) as response:
            return await response.text()


async def request(url, proxy, num_retries=5):
    """
    新建seesion连接，调用协程Response，来获取response.text()
    :param url:
    :param proxy:
    :param num_retries:
    :return:
    """
    async with aiohttp.ClientSession(loop=loop) as session:
        try:
            return await get_response(session, url, proxy)
        except aiohttp.client.ServerDisconnectedError as e:
            response = None
            if num_retries > 0:
                return await request(url, proxy_info, num_retries - 1)
        except aiohttp.client.ClientResponseError as e:
            return str(e)
        except asyncio.TimeoutError as e:
            return str(e)
        except aiohttp.client.ClientConnectorError as e:
            return str(e)


async def download_twitter(url, proxy):
    """
    调用协程request(),获取twitter页返回的text, 解析text,判断是否存在下一页（has_more_items = True）
    若存在，将由min_position来构造下一页的url,调用协程request()来获取其返回的text,直至没有下一页（has_more_items = False）
    最终将返回一个列表response,来存放一页或者多页的内容
    :param url:
    :param proxy:
    :return:response(list)
    """
    prefix = url
    url = prefix
    has_more_items = True
    response = []
    page_num = 1
    while has_more_items is True:
        result = await request(url, proxy)
        if result is not None:
            try:
                json_data = json.loads(result, strict=False)
                has_more_items = json_data.get("has_more_items")
                min_position = json_data.get("min_position")
                url = prefix + min_position
            except json.decoder.JSONDecodeError:
                pass
        response.append(result)
    return response


async def download_url(url, proxy_info):
    """
    调用协程request(),获取response.text..用于不需要翻页的twiiter和普通网页
    """
    response = await request(url, proxy_info)
    return response


async def save_to_dir(dir, filename, url, proxy_info, is_twitter, sem):
    """
    普通页面：将调用协程DownloadURL(), 获取字符串获sponse， 直接存入指定路径
    fullhistory的页面:将调用协程DownloadTwitter()，获取列表response，循环遍历列表，将其存入指定路径，filename将加上列表下标作为后缀（-no）
    :param dir: 存放下载的页面的路径
    :param filename: 来自输入的url_list_filename，其格式为“filename=url”
    :param url: 来自输入的url_list_filename，其格式为“filename=url”
    :return: None
    """
    async with sem:
        full_dir = dir+'/'+filename
        if is_twitter == 0:
            response = await download_url(url, proxy_info)
        else:
            response = await download_twitter(url, proxy_info)
        if response is not None:
            page_num = 1
            for result in response:
                filename_prefix = filename.split('.')[0]
                filename_suffix = filename.split('.')[-1]
                full_dir = dir+'/'+filename_prefix+'-'+str(page_num)+'.'+filename_suffix
                with open(full_dir, 'w') as f:
                    f.write(result)
                page_num += 1


def load_params():
    """
    读取ini文件的任务参数，如若需要proxy，将随机从proxy_list中取出一行
    :return: log_filename, proxy_info, url_list_filename, save_to_directory，is_twitter，subdirectory_length（元组）
    """
    config_dir = sys.argv[1][3:]
    config = configparser.ConfigParser()
    task_info = config.read(config_dir, encoding="utf-8")
    task_name = config_dir.split('/')[-1].split('.')[0]
    now_time = datetime.datetime.now().strftime('%Y-%m-%d')
    config_abspath = os.path.dirname(config_dir)
    os.chdir(config_abspath)
    url_list_filename = config.get("Input", "URL_List_Filename")
    save_to_directory = config.get("Ouput", "Save_To_Directory")
    log_to_directory = config.get("Options", "Log_To_Directory")
    subdirectory_length = int(config.get("Options", "Filename_As_Subdirectory_Prefix_Length"))
    is_twitter = int(config.get("Options", "Is_Twitter"))
    proxy_enable = int(config.get("Proxy", "Proxy_Enable"))
    proxy_list_filename = config.get("Proxy", "Proxy_List_Filename")
    log_filename = log_to_directory+'\\'+task_name+"("+now_time+")"+".txt"

    # 如果需要proxy,将随机从proxy_list文件中获取一行作为proxy
    proxy_info = ""
    if proxy_enable == 1:
        with open(proxy_list_filename, 'r') as f:
            proxy_lines = f.readlines()
            line_count = random.randint(0, len(proxy_lines) - 1)
            proxy_info = proxy_lines[line_count]

    return log_filename, proxy_info, url_list_filename, save_to_directory,is_twitter,subdirectory_length


def bulk_download_urls():
    """
    读取url_list_file， 循环 len(URL_List_Filename) 次, 调用协程函数SaveToDir，将返回的的协程对象存入列表task[];
    :return: task(list)
    """
    global save_to_directory
    with open(url_list_filename, "r") as f:
        URLItems = f.readlines()
        length = len(URLItems)
    tasks = []
    sem = asyncio.Semaphore(50)
    for i in range(length):
        a = URLItems[i]
        str1 = "="
        str1_position = a.index(str1)
        url_position = a.index(str1)+1
        filename = a[:str1_position]
        sub_directory = generate_subdir(filename, subdirectory_length)
        if sub_directory is not None:
            save_to_directory = save_to_directory+'/'+sub_directory
            mkdir(save_to_directory)
        task = asyncio.ensure_future(save_to_dir(save_to_directory, filename, a[url_position:].strip(), proxy_info, is_twitter, sem))
        tasks.append(task)
    return tasks


def mkdir(path):
    """
    输入完整的path，判断是否存在，不存在将生成目录结构path
    """
    path = path.strip()
    path = path.rstrip("\\")
    is_exists = os.path.exists(path)
    if not is_exists:
        os.makedirs(path)
        return True


def generate_subdir(filename, subdirectory_length):
    """
    如filename为file.txt, subdirectory_length为3, 该函数将返回一个结构为： f/i/l/ 的子目录；
    :param filename: 文件名
    :param subdirectory_length: 子目录深度
    :return: 子目录
    """
    if subdirectory_length > 0:
        sub_tmp = list(filename)[:subdirectory_length]
        sub_directory = '/'.join(sub_tmp)
        return sub_directory
    if subdirectory_length > len(filename)-1:
        sub_tmp = list(filename)[:len(filename)-1]
        sub_directory = '/'.join(sub_tmp)
        print("子目录的长度不能大于等于文件名的长度！！ 已默认生成%s级子目录" % (len(filename)-1))
        return sub_directory


if __name__ == '__main__':
    start = time.time()
    #读取ini参数
    ParamsInfo = load_params()
    log_filename = ParamsInfo[0]
    proxy_info = ParamsInfo[1]
    url_list_filename = ParamsInfo[2]
    save_to_directory = ParamsInfo[3]
    is_twitter = ParamsInfo[4]
    subdirectory_length = ParamsInfo[5]

    logging.basicConfig(filename=log_filename, filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)
    # 生成task列表
    tasks = bulk_download_urls()
    # 新建事件循环，用于循环task,直至所有的协程运行完毕，退出循环
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
    print("spend time : %s" % (time.time() - start))
