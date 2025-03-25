"""知乎文章爬虫模块，负责获取知乎文章内容"""

import os
import re
import requests
import random
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class ZhihuCrawler:
    """知乎文章爬虫，用于获取知乎文章内容"""
    
    def __init__(self, use_selenium=False):
        """初始化爬虫
        
        Args:
            use_selenium: 是否使用Selenium渲染页面(更稳定但更慢)
        """
        self.use_selenium = use_selenium
        self.cookies = {
            '_xsrf': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32)),
            '_zap': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789-', k=36)),
            'd_c0': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=|', k=40)),
            'z_c0': f'2|1:0|10:{int(time.time())}|4:z_c0|92:{random.getrandbits(384):x}',
            'KLBRSID': ''.join(random.choices('0123456789abcdef', k=32)) + f'|{int(time.time())}|{int(time.time())}'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Host': 'zhuanlan.zhihu.com',
            'Referer': 'https://www.zhihu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'x-requested-with': 'fetch',
            'x-zse-83': '3_2.0',
            'x-zse-86': '1.0_',
            'x-api-version': '3.0.91',
            'x-udid': 'YNFT1ykiLhqPTpTZ0MgkIHuIwK6-9R214ug=',
            'x-ab-param': '',
            'x-zst-81': '3_2.0',
            'x-request-id': ''.join(random.choices('0123456789abcdef', k=32)),
            'x-zse-93': '101_3_2.0',
            'x-zse-96': '2.0_',
            'x-app-za': 'OS=Mac OS X',
            'x-app-version': '6.12.0',
            'x-referer': 'https://www.zhihu.com/',
            'x-requested-from': 'fetch',
            'x-sgext': ''.join(random.choices('0123456789abcdef', k=8)),
            'x-umt': ''.join(random.choices('0123456789abcdef', k=32))
        }
        self.proxies = {
            'http': os.getenv('ZHIHU_PROXY'),
            'https': os.getenv('ZHIHU_PROXY')
        } if os.getenv('ZHIHU_PROXY') else None
        self.request_timeout = 15
        self.retry_times = 3
        self.request_interval = random.uniform(1, 3)
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否为有效的知乎文章链接
        
        Args:
            url: 知乎文章链接
            
        Returns:
            是否为有效的知乎文章链接
        """
        # 验证URL格式
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
            
            # 验证是否为知乎域名
            if not (parsed_url.netloc == 'zhuanlan.zhihu.com' or parsed_url.netloc == 'www.zhihu.com'):
                return False
            
            # 验证是否包含文章ID
            if 'zhuanlan.zhihu.com' in url and '/p/' in url:
                return True
            elif 'www.zhihu.com' in url and '/question/' in url:
                return True
            else:
                return False
        except:
            return False
    
    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """提取知乎文章内容
        
        Args:
            url: 知乎文章链接
            
        Returns:
            包含文章标题、作者、内容的字典，如果提取失败则返回None
        """
        if not self.validate_url(url):
            raise ValueError(f"无效的知乎文章链接: {url}")
            
        if self.use_selenium:
            return self._extract_with_selenium(url)
        else:
            return self._extract_with_requests(url)
        
    def _extract_with_requests(self, url: str) -> Optional[Dict[str, Any]]:
        """使用requests库提取文章内容"""
        try:
            for attempt in range(self.retry_times):
                try:
                    time.sleep(self.request_interval)
                    response = requests.get(
                        url,
                        headers=self.headers,
                        cookies=self.cookies,
                        proxies=self.proxies,
                        timeout=self.request_timeout
                    )
                    response.raise_for_status()
                    break  # 请求成功则跳出循环
                except requests.exceptions.RequestException as e:
                    if attempt == self.retry_times - 1:
                        raise
                    print(f"请求失败，第{attempt+1}次重试... 错误信息: {str(e)}")
                    self.request_interval *= 1.5  # 指数退避
                    self.headers['User-Agent'] = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{120+attempt}.0.0.0 Safari/537.36'
                    # 更新Cookie以防过期
                    if 'Cookie' in str(e):
                        self.cookies['_xsrf'] = str(random.random())
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取文章标题（更新CSS选择器）
            title = soup.find('h1', {'data-zone': 'title'}).text.strip() if soup.find('h1', {'data-zone': 'title'}) else '未知标题'
            
            # 提取作者信息（更新选择器）
            author_element = soup.find('meta', {'itemprop': 'name'}) or soup.find('a', class_='UserLink-link')
            author = author_element['content'] if author_element and 'content' in author_element.attrs else author_element.text.strip() if author_element else '未知作者'
            
            # 提取文章内容（更新选择器）
            content_element = soup.find('article') or soup.find('div', role='main')
            
            if content_element:
                # 提取所有段落文本
                paragraphs = content_element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs])
            else:
                content = '无法提取文章内容'
            
            # 返回提取结果
            return {
                'title': title,
                'author': author,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            print(f"提取知乎文章失败: {str(e)}")
            return None
    
    def _extract_with_selenium(self, url: str) -> Optional[Dict[str, Any]]:
        """使用Selenium提取文章内容"""
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            
            try:
                driver.get(url)
                time.sleep(3)  # 等待页面加载
                
                # 添加Cookie
                for name, value in self.cookies.items():
                    driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.zhihu.com'
                    })
                
                # 重新加载页面
                driver.get(url)
                time.sleep(3)
                
                # 获取页面内容
                html = driver.page_source
                soup = BeautifulSoup(html, 'lxml')
                
                # 提取信息
                title = soup.find('h1', {'data-zone': 'title'}).text.strip() if soup.find('h1', {'data-zone': 'title'}) else '未知标题'
                author_element = soup.find('meta', {'itemprop': 'name'}) or soup.find('a', class_='UserLink-link')
                author = author_element['content'] if author_element and 'content' in author_element.attrs else author_element.text.strip() if author_element else '未知作者'
                
                content_element = soup.find('article') or soup.find('div', role='main')
                if content_element:
                    paragraphs = content_element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                    content = '\n\n'.join([p.get_text().strip() for p in paragraphs])
                else:
                    content = '无法提取文章内容'
                
                return {
                    'title': title,
                    'author': author,
                    'content': content,
                    'url': url
                }
            finally:
                driver.quit()
        except Exception as e:
            print(f"Selenium提取失败: {str(e)}")
            return None

    def save_as_text(self, article_data: Dict[str, Any], save_dir: str) -> str:
        """将文章内容保存为文本文件
        
        Args:
            article_data: 文章数据字典
            save_dir: 保存目录
            
        Returns:
            保存的文件路径
        """
        if not article_data:
            raise ValueError("文章数据为空")
        
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件名（使用文章标题，去除特殊字符）
        title = article_data['title']
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)  # 替换Windows文件名不允许的字符
        file_name = f"{safe_title}.txt"
        file_path = os.path.join(save_dir, file_name)
        
        # 组织文件内容
        content = f"标题: {article_data['title']}\n"
        content += f"作者: {article_data['author']}\n"
        content += f"链接: {article_data['url']}\n"
        content += f"\n{'-' * 50}\n\n"
        content += article_data['content']
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
