import requests
from lxml import etree
from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import os
import mysql.connector
import tkinter as tk
from tkinter import messagebox
from selenium.webdriver.chrome.service import Service

# 连接数据库
db = mysql.connector.connect(
    host="127.0.0.1",  # 数据库主机地址
    user="root",  # 数据库用户名
    password="123456",  # 数据库密码
    database="manhuaDB"  # 使用的数据库名称
)
cursor = db.cursor()  # 创建游标对象，用于执行SQL查询

# 插入图片到数据库的函数
def insert_image_to_db(comic_name, chapter_name, image_name, image_data, author_name,pingfen):
    sql = "INSERT INTO comic_images (comic_name, chapter_name, image_name, image_data, author_name,pingfen) VALUES (%s, %s, %s, %s, %s,%s)"
    cursor.execute(sql, (comic_name, chapter_name, image_name, image_data, author_name,pingfen))
    db.commit()

# 登录验证函数
def validate_login(username, password):
    # 查询数据库中是否存在对应用户名和密码的记录
    query = "SELECT * FROM user WHERE user_name = %s AND pwd = %s"
    cursor.execute(query, (username, password))  # 执行SQL查询
    result = cursor.fetchone()  # 获取查询结果
    return result is not None  # 如果查询结果不为空，返回True，否则返回False

# 登录界面
def login():
    # 获取输入框中的用户名和密码
    username = entry_username.get()
    password = entry_password.get()

    # 如果登录验证成功
    if validate_login(username, password):
        messagebox.showinfo("Login Success", "Login successful! Starting the crawler...")  # 显示成功消息
        root.destroy()  # 关闭登录窗口
        start_crawler()  # 启动爬虫程序
    else:
        # 如果验证失败，显示错误消息
        messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")

# 启动爬虫的函数
def start_crawler():
    url = 'https://ac.qq.com/'  # 目标漫画网站URL
    data = requests.get(url).text  # 发送请求，获取网页内容
    html = etree.HTML(data)  # 使用lxml解析网页

    comic_list = html.xpath('//a[@class="in-rank-name"]/@href')  # 使用XPath提取漫画链接
    print(comic_list)  # 打印漫画链接列表

    # 遍历提取到的漫画链接
    for comic in comic_list:
        comic_url = url + str(comic)  # 拼接漫画详情页的URL
        url_data = requests.get(comic_url).text  # 请求漫画详情页内容
        data_comic = etree.HTML(url_data)  # 解析漫画详情页

        # 提取漫画名称和作者名称
        name_comic = data_comic.xpath("//h2[@class='works-intro-title ui-left']/strong/text()")[0]  # 提取漫画名称
        # author_name = data_comic.xpath("//span[@class='works-intro-digi']/a/text()")[0]  # 提取作者名称
        # 安全提取作者名称，如果找不到则使用默认值
        author_name_list = data_comic.xpath("//span[@class='first']/em/text()")
        author_name = author_name_list[0] if author_name_list else "未知作者"  # 如果找不到作者，使用 "未知作者"
        pingfen = data_comic.xpath("//strong[@class='ui-text-orange']/text()")[0]
        item_list = data_comic.xpath("//span[@class='works-chapter-item']/a/@href")  # 提取章节链接

        os.makedirs('comic/' + str(name_comic))  # 创建以漫画名称命名的文件夹

        # 遍历漫画章节
        for item in item_list:
            item_url = url + str(item)  # 拼接章节URL
            page_mes = requests.get(item_url).text  # 请求章节页面
            page_ming = etree.HTML(page_mes)  # 解析章节页面
            page_name = page_ming.xpath('//span[@class="title-comicHeading"]/text()')[0]  # 提取章节名称

            os.makedirs('comic/' + str(name_comic) + '/' + str(page_name))  # 创建章节文件夹

            # 设置无界面浏览器选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无界面模式
            chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速

            path = r'F:\jiedan\manhuaPachong\chromedriver-win64\chromedriver.exe'  # chromedriver路径
            service = Service(executable_path=path)  # 使用chromedriver服务
            browser = webdriver.Chrome(service=service)  # 启动Chrome浏览器

            browser.get(item_url)  # 打开章节页面
            sleep(2)  # 等待页面加载

            try:
                # 自动滚动页面以加载图片
                for i in range(1, 100):
                    js = 'var q=document.getElementById("mainView").scrollTop = ' + str(i * 1000)
                    browser.execute_script(js)  # 执行滚动操作
                    sleep(2)  # 等待图片加载

                sleep(2)  # 再次等待加载
                browser.get_screenshot_as_file(str(page_name) + ".png")  # 截图保存页面

                data = browser.page_source  # 获取页面源码
                print(data)  # 打印源码

                # 保存页面源码到本地HTML文件
                fh = open("dongman.html", "w", encoding="utf-8")
                fh.write(data)
                fh.close()  # 关闭文件

                # 使用BeautifulSoup解析本地HTML文件
                html_new = BeautifulSoup(open('dongman.html', encoding='utf-8'), features='html.parser')
                soup = html_new.find(id="mainView")  # 提取页面主体部分

                i = 0  # 初始化图片计数器

                # 遍历图片标签
                for items in soup.find_all("img"):
                    item = items.get("src")  # 获取图片地址
                    comic_pic = requests.get(item).content  # 请求图片

                    try:
                        img_name = f"{i + 1}.jpg"  # 图片文件名
                        # 在插入图片时，保存漫画名、章节名、图片名和作者名还有评分
                        insert_image_to_db(str(name_comic), str(page_name), img_name, comic_pic, author_name,pingfen)

                        print(f"正在下载 {name_comic} - {page_name} - 第 {i + 1} 张图片")  # 打印下载信息
                        i += 1  # 增加图片计数器

                    except Exception as err:
                        print(f"图片下载或保存时出错: {err}")  # 打印错误信息
                        pass

                    if comic_pic:
                        with open('comic/' + str(name_comic) + '/' + str(page_name) + '/' + str(i + 1) + '.jpg',
                                  'wb') as f:
                            f.write(comic_pic)  # 保存图片到本地文件
                            print('正在下载', str(name_comic), '-', str(page_name), '- 第', (i + 1), '张图片')
                            i += 1  # 增加图片计数器

            except Exception as err:
                pass  # 跳过错误

    db.close()  # 关闭数据库连接


# 创建Tkinter窗口
root = tk.Tk()
root.title("Login")  # 设置窗口标题

# 用户名输入框
label_username = tk.Label(root, text="Username:")
label_username.grid(row=0, column=0, padx=10, pady=10)  # 布局用户名标签
entry_username = tk.Entry(root)
entry_username.grid(row=0, column=1, padx=10, pady=10)  # 布局用户名输入框

# 密码输入框
label_password = tk.Label(root, text="Password:")
label_password.grid(row=1, column=0, padx=10, pady=10)  # 布局密码标签
entry_password = tk.Entry(root, show="*")
entry_password.grid(row=1, column=1, padx=10, pady=10)  # 布局密码输入框

# 登录按钮
login_button = tk.Button(root, text="Login", command=login)  # 创建登录按钮，并绑定login函数
login_button.grid(row=2, column=0, columnspan=2, pady=10)  # 布局登录按钮

# 启动Tkinter主循环
root.mainloop()  # 进入事件循环
