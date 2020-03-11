FastDownloader是一个IO异步的URL下载器, 可以读取url_list.txt,批量将其下载到指定的目录下;


## Requirements
- Python 3.7;
- asyncio;
- aiohttp;
- configparser;
- logging;
- elasticsearch;
- random;
- sys ;
- datetime;
- os;
- json;
- async_timeout;


## Basic Example

#任务参数写在ini文件中,ini格式如下,以下路径支持相对路径和绝对路径：

[Input]
URL_List_Filename=D:\Program Files\PycharmProjects\Python_Project\FastDownloader\Input\url_list.txt

[Ouput]

Save_To_Directory=D:\Program Files\PycharmProjects\Python_Project\FastDownloader\Result

[Options]
Log_To_Directory=D:\Program Files\PycharmProjects\Python_Project\FastDownloader\Log
Filename_As_Subdirectory_Prefix_Length=0
Is_Twitter=1

#Filename_As_Subdirectory_Prefix_Length：根据filename建立子目录，0则不建立目录
#Is_Twitter： twiter的full history,为1程序将处理翻页，输入的filename将加上-no

[Proxy]
Proxy_Enable=1
Proxy_List_Filename=D:\KWM\Common\WebDataMinerOperation\ProxyList.txt


#url_list.txt格式如下,一行一个

filename=url (BaiduHomepage.html=http://www.baidu.com)


#调用方式：命令行； 格式如下


相对路径：

python FastDownloader.exe /t=/"./task.ini"

绝对路径：

python FastDownloader.exe /t=/"D:/Program Files/PycharmProjects/Python_Project/FastDownloader/task.ini"






