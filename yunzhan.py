##下载链接支持以下两种
## https://book.eol.cn/books/xxxx/mobile/index.html
## https://book.yunzhan365.com/xxxx/xxxx/mobile/index.html

##自行安装相关库

## 注意：某些文件并未匹配

from PIL import Image
from io import BytesIO
import requests
import re
import os
import PIL

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

# 创建会话，保持连接
session = requests.session()

def download_image(image_url, base_url, page_num, total_pages):
    """
    下载单个图片并显示进度
    """
    # 清理和构造完整的图片URL
    image_url = image_url.strip().replace('..\\', '').replace('\\', '/').replace('//', '/').lstrip('/')
    full_url = f"{base_url.rstrip('/')}/files/large/{image_url}"
    
    try:
        response = session.get(full_url, headers=headers, timeout=30)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        # 显示下载进度
        progress = (page_num + 1) / total_pages
        bar_length = 50
        filled_length = int(round(bar_length * progress))
        bar = "#" * filled_length + "-" * (bar_length - filled_length)
        print(f"\r下载进度: [{bar}] {progress:.2%}", end='', flush=True)
        
        return img
    except (requests.RequestException, PIL.UnidentifiedImageError) as e:
        print(f"\n下载图片 {page_num+1} 时出错: {str(e)}")
        return None

def process_book(book_url):
    """
    处理单本书籍的下载和PDF生成
    """
    try:
        # 验证URL格式
        if not book_url.startswith(('https://book.eol.cn/', 'https://book.yunzhan365.com/')):
            print("URL格式不正确，请检查！")
            return
            
        # 获取初始页面
        response = session.get(book_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 提取基础URL
        url_parts = book_url.split('/')
        if len(url_parts) >= 5:
            base_url = '/'.join(url_parts[:5])
        else:
            print("无法提取基础URL")
            return
        
        # 提取配置文件URL
        config_match = re.findall('src="javascript/config.js\?(.+?)"></script>', response.text, re.S)
        if config_match:
            config_url = f'{book_url.rsplit("/", 1)[0]}/javascript/config.js?{config_match[0]}'
            config_response = session.get(config_url, headers=headers, timeout=30)
            config_response.raise_for_status()
            
            # 提取书籍标题和图片URL
            title_match = re.findall('"title":"(.+?)"', config_response.text)
            image_urls_match = re.findall('"n":\[\"(.+?)\"\]', config_response.text)
            
            if not title_match or not image_urls_match:
                print("未能提取到书籍标题或图片URL")
                return
                
            title = title_match[0]
            # 清理标题中的非法字符
            title = re.sub(r'[\\/:*?"<>|]', '_', title)
            image_urls = image_urls_match
            
            print(f"书籍名称：{title}.pdf / 总页数：{len(image_urls)}页")
            
            # 下载图片
            images = []
            for page_num, image_url in enumerate(image_urls):
                img = download_image(image_url, base_url, page_num, len(image_urls))
                if img:
                    images.append(img)
            
            print('\n开始制作并合并成PDF...')
            if images:
                # 创建保存路径（确保中文路径可用）
                pdf_path = f"./{title}.pdf"
                # 保存PDF
                images[0].save(
                    pdf_path, 
                    "PDF", 
                    resolution=150.0,  # 提高分辨率
                    save_all=True, 
                    append_images=images[1:],
                    quality=95  # 提高图片质量
                )
                print(f"PDF生成完成！保存路径：{os.path.abspath(pdf_path)}")
            else:
                print("没有成功下载任何图片，无法生成PDF")
        else:
            print(f"{book_url} - 未能找到配置文件，请确认链接是否有效")
    except requests.RequestException as e:
        print(f"访问网站时出错: {str(e)}")
    except Exception as e:
        print(f"发生意外错误: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息

if __name__ == '__main__':
    print("=== 电子书下载工具 ===")
    print("支持的链接格式：")
    print("1. https://book.eol.cn/books/xxxx/mobile/index.html")
    print("2. https://book.yunzhan365.com/xxxx/xxxx/mobile/index.html")
    print("输入 'q' 退出程序\n")
    
    while True:
        book_url = input("请输入书本网址：")
        if book_url.lower() == 'q':
            break
        
        # 处理用户输入的链接（去除首尾空格）
        book_url = book_url.strip()
        if not book_url:
            continue
            
        # 下载指定的书籍
        process_book(book_url)
        
        # 询问是否继续
        while True:
            choice = input("\n是否继续下载其他书本? (y/n): ")
            if choice.lower() in ['y', 'n']:
                break
            print("请输入 y 或 n！")
        
        if choice.lower() != 'y':
            break
    
    print("\n程序已退出")
