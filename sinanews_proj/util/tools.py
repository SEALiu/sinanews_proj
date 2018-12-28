import hashlib
import re

from urllib import parse
from bs4 import BeautifulSoup


def html_pretty(html):
    """
    去掉html中的所有换行符和tabs
    :param html: 网页html
    :return: pretty html
    """
    regex = r'[^\n\t]'
    matches = re.finditer(regex, html, re.MULTILINE)
    content = ''
    for match in matches:
        content += match.group()

    return content


def html_pure(html):
    """
    去掉html中所有节点的属性，但保留图片的src属性
    :param html: 网页html
    :return: pure html
    """
    content_soup = BeautifulSoup(html, features="lxml")
    for node in content_soup.find_all():
        for key in list(node.attrs.keys()):
            if key != 'src' and key != 'data-src' and key != 'style':
                # 删除除src，data-src，style之外的属性
                del node[key]
            if key == 'style' and 'none' in node[key]:
                # 删除含有style='display:none'的元素（因为不可见）
                node.extract()
            elif key == 'style':
                # 如果 style 中没有 display:none，则删除属性即可
                del node[key]

    return str(content_soup)


def imgsrc_2_osshash(content: str, response_url: str, upload_base_path: str) -> dict:
    """
    将html中img的src链接替换成hash，并使用hash名作为oss的文件名称
    :param content: 文章内容的html
    :param response_url: 网页的response来源url
    :param upload_base_path: oss的上传路径
    :return: 字典 {'html':'将替换src链接替换成hash后的文章内容', 'oss-hash': 'src下载链接'}
    """
    src_dict = dict()
    content_soup = BeautifulSoup(content, features="lxml")
    url_info = parse.urlparse(response_url)

    for node in content_soup.find_all():
        for key in list(node.attrs.keys()):
            if key == 'src':
                img_d_url = node[key]
                if img_d_url.startswith('http'):
                    pass
                elif img_d_url.startswith('//'):
                    # img src 缺少协议（http/https），需要补全
                    img_d_url = '{}:{}'.format(url_info.scheme, img_d_url)
                elif img_d_url.startswith('data:') and 'data-src' in node.attrs:
                    # sina.cn 使用 data:image/png(jpeg) 做占位符, 真正的图片链接在 data-src 属性中
                    # 从 data-src 中读取数据，如果是'//'开头，那么使用response.url的协议进行补全
                    img_d_url = node['data-src']
                    if img_d_url.startswith('//'):
                        img_d_url = '{}:{}'.format(url_info.scheme, img_d_url)
                else:
                    # img src 是当前url下的相对路径，需要补全
                    img_d_url = '{scheme}://{netloc}{path}'.format(
                        scheme=url_info.scheme,
                        netloc=url_info.netloc,
                        path=img_d_url)

                hash_temp = hashlib.sha1(img_d_url.encode('utf-8')).hexdigest()
                node['src'] = 'https://oss.lano.fate.kim/{upload_base_path}{filename}'.format(
                    upload_base_path=upload_base_path,
                    filename=hash_temp
                )
                src_dict[hash_temp] = img_d_url

    src_dict['html'] = str(content_soup)
    return src_dict


def src2osshash(src: str, response_url: str, upload_base_path: str) -> dict:
    img_d_url = src
    url_info = parse.urlparse(response_url)
    if img_d_url.startswith('http'):
        pass
    elif img_d_url.startswith('//'):
        # img src 缺少协议（http/https），需要补全
        img_d_url = '{}:{}'.format(url_info.scheme, img_d_url)
    else:
        # img src 是当前url下的相对路径，需要补全
        img_d_url = '{scheme}://{netloc}{path}'.format(
            scheme=url_info.scheme,
            netloc=url_info.netloc,
            path=img_d_url)

    hash_temp = hashlib.sha1(img_d_url.encode('utf-8')).hexdigest()

    return {
        'image_download_url': img_d_url,
        'hash': hash_temp,
        'oss_link': 'https://oss.lano.fate.kim/{upload_base_path}{filename}'.format(
            upload_base_path=upload_base_path,
            filename=hash_temp
        )
    }
