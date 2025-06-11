# 🕵️‍♂️ 东方财富网股吧爬虫

> 本项目为一个基于 Python 的网络爬虫程序，用于从 [东方财富网股吧](https://guba.eastmoney.com/) 爬取帖子信息。该项目使用多代理IP技术绕过网站的反爬机制，确保稳定高效地获取公开数据。

## 📌 项目说明

本爬虫通过使用多个代理IP的手段，实现了对东方财富网股吧页面中公开帖子内容的抓取。所有数据仅供学习研究使用，请勿用于非法用途或商业传播。
## 🔧 功能特性

- ✅ 支持多IP绕过网站反爬机制  
- ✅ 使用随机 User-Agent 和 Referer 模拟浏览器访问  
- ✅ 多代理IP轮换防止 IP 被封禁  
- ✅ 可配置爬取目标板块、关键词、页码范围  
- ✅ 数据保存为 JSON 或 CSV 格式  
- ✅ 日志记录与异常处理机制  

## 📦 技术栈

- Python 3.x
- 第三方库：
  - `requests`
  - `BeautifulSoup4`
  - `fake_useragent`
  - `pandas`

---

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 fake-useragent
```

> ⚠️ 注意：`fake-useragent` 需要联网下载 ua 数据，或手动设置本地 ua.json。

### 2. 修改配置

在requestproxy.py中 请根据自己的代理IP的请求商来修改get_proxy函数，该函数获取一个代理IP和port。这里笔者用的是巨量IP代理，使用这个的时候配置一下将APIKEY复制进去就可以直接用了。如果使用的其他代理商，请根据他们的返回格式重写这个函数

### 3. 运行爬虫

```bash
python main.py --stock-code 300750 --total-pages 100 --threads-count 4 --mode crawl
python main.py --stock-code 300750 --total-pages 100 --threads-count 4 --mode complete
```
complete模式需要多次运行
然后注释掉
## ⚠️ 合法性与伦理声明

> **本项目仅供学习交流使用，严禁用于任何非法用途或商业用途！**

在使用本爬虫之前，请务必遵守以下原则：

- ✔️ **尊重网站 Robots 协议**
- ✔️ **不得频繁请求造成服务器压力过大**
- ✔️ **不爬取非公开或受保护的数据**
- ✔️ **禁止将爬取结果用于恶意分析、传播谣言或操纵市场行为**

如需大规模采集数据，请联系网站官方申请合法接口权限。

> **本项目遵循 MIT License 开源协议，保留原作者信息即可自由使用。**

