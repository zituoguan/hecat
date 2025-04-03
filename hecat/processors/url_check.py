"""url_check 处理器
检查数据中的死链接（HTTP 错误代码、超时、SSL/TLS 错误...）

# .hecat.yml
steps:
  - name: 检查 URL
    module: processors/url_check
    module_options:
      source_directories: # (默认 []) 检查这些目录下所有 .yml 文件中的 URL
        - tests/awesome-selfhosted-data/software
        - tests/awesome-selfhosted-data/tags
      source_files: # (默认 []) 检查这些文件中的 URL
        - tests/shaarli.yml
        - tests/awesome-selfhosted-data/licenses.yml
      check_keys: # (默认 ['url', 'source_code_url', 'website_url', 'demo_url']) 包含要检查的 URL 的 YAML 键（如果存在）
        - url
        - source_code_url
        - website_url
        - demo_url
      errors_are_fatal: False # (默认 False) 如果为 True，则在处理结束时，如果有任何检查失败，则以错误代码 1 退出
      exclude_regex: # (默认 []) 不检查匹配这些正则表达式的 URL
        - '^https://github.com/[\w\.\-]+/[\w\.\-]+$' # 不检查将由 github_metadata 模块处理的 URL
        - '^https://www.youtube.com/watch.*$' # 不检查 YouTube 视频 URL，即使对于不可用的视频也总是返回 HTTP 200
"""

import sys
import ruamel.yaml
import logging
import re
from ..utils import load_yaml_data
import requests

VALID_HTTP_CODES = [200, 206]
# INVALID_HTTP_CODES = [403, 404, 500]

def check_return_code(url, current_item_index, total_item_count, errors):
    try:
        # 当可能时只获取前 200 字节，不支持 Range: 头的服务器将简单地返回整个页面
        response = requests.get(url, headers={"Range": "bytes=0-200", "User-Agent": "hecat/0.0.1"}, timeout=10)
        if response.status_code in VALID_HTTP_CODES:
            logging.info('[%s/%s] %s HTTP %s', current_item_index, total_item_count, url, response.status_code)
            return True
        else:
            error_msg = '{} : HTTP {}'.format(url, response.status_code)
            logging.error('[%s/%s] %s', current_item_index, total_item_count, error_msg)
            errors.append(error_msg)
            return False
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, requests.exceptions.ContentDecodingError, requests.exceptions.TooManyRedirects) as connection_error:
        error_msg = '{} : {}'.format(url, connection_error)
        logging.error('[%s/%s] %s', current_item_index, total_item_count, error_msg)
        errors.append(error_msg)
        return False

def check_urls(step):
    data = []
    errors = []
    checked_urls = []
    if 'exclude_regex' not in step['module_options'].keys():
        step['module_options']['exclude_regex'] = []
    if 'source_directories' not in step['module_options'].keys():
        step['module_options']['source_directories'] = []
    if 'source_files' not in step['module_options'].keys():
        step['module_options']['source_files'] = []
    if 'check_keys' not in step['module_options'].keys():
        step['module_options']['check_keys'] = ['url', 'source_code_url', 'website_url', 'demo_url']
    for source_dir_or_file in step['module_options']['source_directories'] + step['module_options']['source_files']:
        new_data = load_yaml_data(source_dir_or_file)
        data = data + new_data
    total_item_count = len(data)
    logging.info('已加载 %s 个项目', total_item_count)
    skipped_count = 0
    success_count = 0
    error_count = 0
    current_item_index = 1
    for item in data:
        for key_name in step['module_options']['check_keys']:
            try:
                if any(re.search(regex, item[key_name]) for regex in step['module_options']['exclude_regex']):
                    logging.info('[%s/%s] 跳过 URL %s，匹配排除正则表达式', current_item_index, total_item_count, item[key_name])
                    skipped_count = skipped_count + 1
                    continue
                else:
                    if item[key_name] not in checked_urls:
                        if check_return_code(item[key_name], current_item_index, total_item_count, errors):
                            success_count = success_count + 1
                        else:
                            error_count = error_count + 1
                        checked_urls.append(item[key_name])
            except KeyError:
                pass
        current_item_index = current_item_index + 1
    logging.info('处理完成。成功: %s - 跳过: %s - 错误: %s', success_count, skipped_count, error_count)
    if errors:
        logging.error("处理过程中出现错误")
        print('\n'.join(errors))
        if 'errors_are_fatal' in step['module_options'].keys() and step['module_options']['errors_are_fatal']:
            sys.exit(1)
