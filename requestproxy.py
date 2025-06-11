import requests
from fake_useragent import UserAgent
from threading import Thread,Lock,BoundedSemaphore
import json
import re
from typing import Dict, List
from bs4 import BeautifulSoup
import logging
import time
import os
from queue import Queue

import random

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)
lock = Lock()
semaphore = BoundedSemaphore(5)

def get_proxy():
    api_url = 'http*******************'
    try:
        time.sleep(0.2)
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = json.loads(response.content)
        proxy_list = data.get('data', [])
        proxy_list = proxy_list.get('proxy_list',[])
        item = proxy_list[0]
        if isinstance(item, str) and ':' in item:
            ip, remain = item.split(':', 1)
            port = remain.split(',')[0]
            return f"http://{ip}:{port}"
    except Exception as e:
        logger.error(f"获取代理失败: {e}")
    return None

def get_url(stock,page):
    return f"https://guba.eastmoney.com/list,{stock}_{page}.html"

def extract_posts(data: Dict,stock_num:int) -> List[Dict]:
    """Extract and format post information from raw data."""
    posts = []
    for post in data.get('re', []):
        try:
            title = post.get('post_title', '').strip()
            # if isinstance(title, bytes):
            #     title = title.decode('utf-8')
            post_info = {
                'id': post.get('post_id'),
                'title': post['post_title'],
                'author': post.get('user_nickname', '').strip(),
                'click_count': post.get('post_click_count', 0),
                'comment_count': post.get('post_comment_count', 0),
                'publish_time': post.get('post_publish_time', ''),
                'last_time': post.get('post_last_time', ''),
                'source_url': f"https://guba.eastmoney.com/news,{stock_num},{post.get('post_id')}.html"
            }
            posts.append(post_info)
        except (KeyError, AttributeError) as e:
            logger.warning(f"Skipping malformed post: {str(e)}")
    return posts

def parse_page(page_source: str, page: int,stock_num:int) -> List[Dict]:
    soup = BeautifulSoup(page_source, 'html.parser')
    script_tags = soup.find_all('script')
    
    for script in script_tags:
        if script.string and 'var article_list' in script.string:
            try:
                match = re.search(r'var article_list\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    json_str = re.sub(r',\s*}(?=\s*$)', '}', json_str)
                    json_str = re.sub(r',\s*](?=\s*$)', ']', json_str)
                    data = json.loads(json_str)
                    return extract_posts(data,stock_num)
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.error(f"解析页面{page}错误: {str(e)}")
                continue
def get_page(stock, page, proxy):
    headers = {
        'User-Agent': UserAgent().random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
    }
    
    proxies = {
        "http": proxy,
        "https": proxy
    }
    
    url = get_url(stock, page)
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        print(f"Page {page} of stock {stock} fetched successfully.")
        return response.content.decode()
    except Exception as e:
        print(f"Failed to fetch page {page} of stock {stock}: {e}")

def save_to_json(posts: List[Dict], file_path: str):
    """将帖子信息保存到 JSON 文件中"""
    with lock:
        if os.path.exists(file_path):
            # 如果文件已存在，追加数据
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_data.extend(posts)
            posts = existing_data

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
        logger.info(f"数据已保存到 {file_path}")

def load_progress(progress_file: str) -> int:
    """从进度文件中加载已爬取的最大页数"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                pass
    return 0  # 如果文件不存在或内容无效，返回 0

def update_progress(progress_file: str, current_page: int):
    """更新进度文件中的最大页数"""
    with open(progress_file, 'a+', encoding='utf-8') as f:
        f.write(str(current_page)+'\n')
    logger.info(f"进度已更新到 {progress_file}，当前页数：{current_page}")

def process_pages(stock_code: str, start_page: int, end_page: int, output_file: str):
    """处理指定范围内的多个页面"""
    semaphore.acquire()  # 获取信号量，控制并发线程数
    proxy = get_proxy()
    if not proxy:
        logger.error("未能获取代理 IP，跳过线程创建。")
        semaphore.release()
        return
    try:
        for page in range(start_page, end_page + 1):
            page_source = get_page(stock_code, page, proxy)
            if not page_source:
                logger.error(f"无法获取页面源码，跳过页面 {page}。")
                continue

            posts = parse_page(page_source, page, stock_code)
            if posts:
                logger.info(f"成功提取页面 {page} 的 {len(posts)} 条帖子信息。")
                save_to_json(posts, output_file)
                update_progress("./log", page)

            else:
                logger.warning(f"页面 {page} 未提取到任何帖子信息。")

            # 添加延迟，保护服务器
            time.sleep(abs(random.uniform(3,7)))
    finally:
        semaphore.release()  # 释放信号量


def main(stock_code: str, total_pages: int, pages_per_thread: int):
    """主函数：动态分配任务给多个线程"""
    output_file = f"{stock_code}_posts.json"
    threads = []
    num_threads = total_pages // pages_per_thread + (1 if total_pages % pages_per_thread != 0 else 0)

    for i in range(num_threads):
        # 每个线程获取一个代理 IP
        # 计算当前线程负责的页数范围
        start_page = i * pages_per_thread + 1
        end_page = min((i + 1) * pages_per_thread, total_pages)

        # 创建线程
        thread = Thread(target=process_pages, args=(stock_code, start_page, end_page, output_file))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

def process_missing_pages(stock_code: str, pages: list, output_file: str):
    """处理缺失的多个页面"""
    semaphore.acquire()  # 获取信号量，控制并发线程数
    proxy = get_proxy()
    if not proxy:
        logger.error("未能获取代理 IP，跳过线程创建。")
        semaphore.release()
        return
    
    try:
        for page in pages:
            page_source = get_page(stock_code, page, proxy)
            if not page_source:
                logger.error(f"无法获取页面源码，跳过页面 {page}。")
                continue

            posts = parse_page(page_source, page, stock_code)
            if posts:
                logger.info(f"成功提取页面 {page} 的 {len(posts)} 条帖子信息。")
                save_to_json(posts, output_file)
                update_progress("./log", page)
            else:
                logger.warning(f"页面 {page} 未提取到任何帖子信息。")

            # 添加延迟，保护服务器
            time.sleep(abs(random.uniform(3,7)))
    finally:
        semaphore.release()  # 释放信号量

def crawl_missing_pages(stock_code: str, missing_pages: list, batch_size: int = 20):
    """主函数：多线程爬取缺失的页面"""
    output_file = f"{stock_code}_posts.json"
    threads = []
    
    # 将缺失的页面分成批次，每个线程处理一个批次
    for i in range(0, len(missing_pages), batch_size):
        batch = missing_pages[i:i + batch_size]
        
        # 创建线程
        thread = Thread(
            target=process_missing_pages, 
            args=(stock_code, batch, output_file)
            )
        threads.append(thread)
        thread.start()
        time.sleep(1)  # 稍微延迟一下，避免同时创建太多线程

    # 等待所有线程完成
    for t in threads:
        t.join()
        
if __name__ =='__main__':
    # 测试参数
    stock_code = "300750"   # 贵州茅台股票代码
    total_pages = 3300       # 总页数
    threads_count = 5       # 线程数（每个线程爬取 20 页）

    # 爬取页面
    # main(stock_code, total_pages, threads_count)
    
    # 爬取没有爬到的页面
    try:
        with open("./log", "r", encoding='utf-8') as f:
            codes = f.read().split('\n')
    except FileNotFoundError:
        codes = []
    
    # 处理并找出缺失的页码
    codes = list(set(codes))
    codes = [int(i) for i in codes if i.isdigit()]
    codes.sort()
    
    missing_pages = []
    for i in range(1, total_pages + 1):
        if i not in codes:
            print(f"缺失页码：{i}")
            missing_pages.append(i)
    
    print(f"共发现 {len(missing_pages)} 个缺失页面")
    
    if missing_pages:
        # 开始爬取缺失的页面
        crawl_missing_pages(stock_code, missing_pages)
        print("缺失页面爬取完成！")
    else:
        print("没有缺失页面需要爬取。")
        print("没有缺失页面需要爬取。")








