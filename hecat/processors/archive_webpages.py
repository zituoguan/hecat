"""归档网页
下载数据文件中项目的 'url:' 键指向的网页的本地存档。该模块设计用于归档 Shaarli 实例的书签。
您可能需要先使用 importers/shaarli_api 模块将数据从 Shaarli 导入到 hecat。
每个网页保存在以项目 'id' 键命名的单独目录中，位于模块选项中配置的输出目录下。
exporters/html_table 模块将在输出的 HTML 列表中显示网页本地副本的链接。

请注意，您可能需要设置系统范围的广告拦截机制，以防止 wget 下载
广告和烦人内容，从而节省带宽和磁盘空间。参见
https://gitlab.com/nodiscc/toolbox/-/tree/master/ARCHIVE/ANSIBLE-COLLECTION/roles/adblock_hosts 或
手动设置。使用 dns=dnsmasq 模式的 NetworkManager 示例：
$ sudo mkdir /var/lib/dnsmasq
$ sudo wget -O /var/lib/dnsmasq/unified-hosts.txt https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
$ echo 'addn-hosts=/var/lib/dnsmasq/unified-hosts.txt' | sudo tee /etc/NetworkManager/dnsmasq.d/adblock
$ sudo systemctl reload NetworkManager

由于输出目录可能因存档的页面众多而变得非常大，您可以使用 jdupes 对文件进行去重并硬链接相同的文件：
$ jdupes --link-hard --recurse /path/to/archive/directory/

# $ cat tests/.hecat.archive_webpages.yml
steps:
  - name: 归档网页
    module: processors/archive_webpages
    module_options:
      data_file: tests/shaarli.yml # YAML 数据文件的路径
      only_tags: ['doc'] # 仅下载带有所有这些标签的项目
      exclude_tags: ['nodl'] # (默认 [])，不下载带有任何这些标签的项目
      exclude_regex: # (默认 []) 不归档匹配这些正则表达式的 URL
        - '^https://[a-z]\.wikipedia.org/wiki/.*$' # 不归档维基百科页面，假设您有来自 https://dumps.wikimedia.org/ 的维基百科转储的本地副本
      output_directory: 'tests/webpages' # 归档页面的输出目录路径
      skip_already_archived: True # (默认 True) 当项目已有 'archive_path': 键时跳过处理
      clean_removed: True # (默认 False) 移除不匹配数据文件中任何 id 的现有归档页面
      clean_excluded: True # (默认 False) 移除匹配 exclude_regex 的现有归档页面
      skip_failed: False # (默认 False) 不尝试归档上次尝试失败的项目 (archive_error: True)

# $ hecat --config tests/.hecat.archive_webpages.yml

数据文件格式（import_shaarli 模块的输出）：
# shaarli.yml
- id: 1234 # 必需，唯一标识
  url: https://solar.lowtechmagazine.com/2016/10/pigeon-towers-a-low-tech-alternative-to-synthetic-fertilizers
  tags:
    - tag1
    - tag2
    - diy
    - doc
    - readlater
  ...
  private: false
  archive_path: 1234/solar.lowtechmagazine.com/2016/...-fertilizers.html # (自动添加) 本地归档页面的路径，相对于 output_directory/{public,private}/

源目录结构：
└── shaarli.yml

输出目录结构：
└── webpages/
    ├── public/
    │   ├── 1234/ # YAML 文件中项目的 id
    │   │   └── solar.lowtechmagazine.com/
    │   │       └── 2016/
    │   │           └── .../
    │   │               ├── index.html # 镜像原始网站的文件/目录结构
    │   │               ├── .../
    │   │               └── image.jpg
    │   ├── 1235/
    │   ├── 1236/
    │   └── ...
    └── private/
        ├── 5678/
        ├── 91011/
        └── ...

"""

import sys
import os
import logging
import subprocess
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote, quote
import ruamel.yaml
from ..utils import load_yaml_data, write_data_file

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=2, offset=0)
yaml.width = 99999

def wget(step, item, wget_output_directory):
    """使用 wget 归档网页，返回归档文件的本地路径"""
    try:
        os.mkdir(wget_output_directory)
    except FileExistsError:
        pass
    wget_process = subprocess.Popen(['/usr/bin/wget',
                                     '--continue',
                                     '--span-hosts',
                                     '--adjust-extension',
                                     '--timestamping',
                                     '--convert-links',
                                     '--page-requisites',
                                     '--no-verbose',
                                     '--timeout=30',
                                     '--tries=3',
                                     '-e', 'robots=off',
                                     '--user-agent="Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"',
                                     item['url']],
                                   cwd=wget_output_directory,
                                   stdout=sys.stdout,
                                   stderr=sys.stderr,
                                   universal_newlines=True)
    wget_process.communicate()
    archive_relative_path = wget_output_path(item, wget_output_directory)
    if archive_relative_path is not None:
        local_archive_path = quote(str(item['id']) + '/' + archive_relative_path)
    else:
        local_archive_path = None
        logging.error('归档 %s 时出错', item['url'])
    return local_archive_path

# 改编自 https://github.com/ArchiveBox/ArchiveBox/blob/master/archivebox/extractors/wget.py，MIT 许可证
def wget_output_path(item, wget_output_directory):
    """计算 wget 下载的 .html 文件的路径，因为 wget 可能
    调整一些路径，使其与 base_url 路径不同。
    参见 wget --adjust-extension (-E) 的文档
    """
    # Wget 下载可以根据 url 以多种不同方式保存：
    #    https://example.com
    #       > example.com/index.html
    #    https://example.com?v=zzVa_tX1OiI
    #       > example.com/index.html?v=zzVa_tX1OiI.html
    #    https://www.example.com/?v=zzVa_tX1OiI
    #       > example.com/index.html?v=zzVa_tX1OiI.html
    #    https://example.com/abc
    #       > example.com/abc.html
    #    https://example.com/abc/
    #       > example.com/abc/index.html
    #    https://example.com/abc?v=zzVa_tX1OiI.html
    #       > example.com/abc?v=zzVa_tX1OiI.html
    #    https://example.com/abc/?v=zzVa_tX1OiI.html
    #       > example.com/abc/index.html?v=zzVa_tX1OiI.html
    #    https://example.com/abc/test.html
    #       > example.com/abc/test.html
    #    https://example.com/abc/test?v=zzVa_tX1OiI
    #       > example.com/abc/test?v=zzVa_tX1OiI.html
    #    https://example.com/abc/test/?v=zzVa_tX1OiI
    #       > example.com/abc/test/index.html?v=zzVa_tX1OiI.html
    # 对于带有查询和哈希片段或扩展名（如 shtml / htm / php 等）的页面，URL 编码和重命名的方式也非常复杂
    # 由于 wget 算法对于 -E（附加 .html）非常复杂
    # 而且无法从 wget 获取计算后的输出路径
    # 为了避免必须逆向工程他们的计算方式，
    # 我们只是在输出文件夹中查看并从文件系统中读取 wget 使用的文件名
    without_fragment = urlparse(item['url'])._replace(fragment='').geturl().strip('//')
    without_query = urlparse(without_fragment)._replace(query='').geturl().strip('//')
    domain = urlparse(item['url']).netloc
    full_path = without_query.strip('/')
    search_dir = Path(wget_output_directory + '/' + domain.replace(":", "+") + unquote(urlparse(item['url']).path))
    for _ in range(4):
        if search_dir.exists():
            if search_dir.is_dir():
                html_files = [
                    f for f in search_dir.iterdir()
                    if re.search(".+\\.[Ss]?[Hh][Tt][Mm][Ll]?$", str(f), re.I | re.M)
                ]
                if html_files:
                    return str(html_files[0].relative_to(wget_output_directory))
                # 有时 wget 下载的 URL 没有扩展名并返回非 html 内容
                # 例如 /some/example/rss/all -> 一些 RSS XML 内容)
                #      /some/other/url.o4g   -> 一些二进制未识别扩展名)
                # 使用 archivebox add --depth=1 https://getpocket.com/users/nikisweeting/feed/all 测试
                last_part_of_url = unquote(full_path.rsplit('/', 1)[-1])
                for file_present in search_dir.iterdir():
                    if file_present == last_part_of_url:
                        return str((search_dir / file_present).relative_to(wget_output_directory))
        # 向上移动一个目录级别
        search_dir = search_dir.parent
        if str(search_dir) == wget_output_directory:
            break
    # 检查是否存在任何不是空文件夹的文件
    domain_dir = Path(domain.replace(":", "+"))
    files_within = list((Path(wget_output_directory) / domain_dir).glob('**/*.*'))
    if files_within:
        return str((files_within[-1]))
    # 回退到仅域名目录
    search_dir = Path(wget_output_directory) / domain.replace(":", "+")
    if search_dir.is_dir():
        return domain.replace(":", "+")
    return None

def archive_webpages(step):
    """归档从每个项目的 'url' 链接的网页，如果它们的标签匹配 step['only_tags'] 中的一个，
    为每个下载的项目将本地归档的路径写入原始数据文件中的新键 'archive_path'
    """
    downloaded_count = 0
    skipped_count = 0
    error_count = 0
    for visibility in ['/public', '/private']:
        try:
            os.mkdir(step['module_options']['output_directory'] + visibility)
        except FileExistsError:
            pass
    items = load_yaml_data(step['module_options']['data_file'])
    if 'clean_removed' not in step['module_options']:
        step['module_options']['clean_removed'] = False
    if 'skip_failed' not in step['module_options']:
        step['module_options']['skip_failed'] = False
    for item in items:
        if item['private']:
            local_archive_dir = step['module_options']['output_directory'] + '/private/' + str(item['id'])
        else:
            local_archive_dir = step['module_options']['output_directory'] + '/public/' + str(item['id'])
        # 当 skip_already_archived: True 时跳过已归档的项目
        if (('skip_already_archived' not in step['module_options'].keys() or
                step['module_options']['skip_already_archived']) and 'archive_path' in item.keys() and item['archive_path'] is not None):
            logging.debug('跳过 %s (id %s): 已归档', item['url'], item['id'])
            skipped_count = skipped_count +1
        # 跳过匹配 exclude_tags 的项目
        elif ('exclude_tags' in step['module_options'] and any(tag in item['tags'] for tag in step['module_options']['exclude_tags'])):
            logging.debug('跳过 %s (id %s): 一个或多个标签存在于 exclude_tags 中', item['url'], item['id'])
            skipped_count = skipped_count +1
        # 跳过匹配 exclude_regex 的项目
        elif ('exclude_regex' in step['module_options'] and any(re.search(regex, item['url']) for regex in step['module_options']['exclude_regex'])):
            logging.debug('跳过 %s (id %s): URL 匹配 exclude_regex', item['url'], item['id'])
            skipped_count = skipped_count +1
            if 'clean_excluded' in step['module_options'] and step['module_options']['clean_excluded']:
                if os.path.isdir(local_archive_dir):
                    logging.info('移除本地归档目录 %s', local_archive_dir)
                    shutil.rmtree(local_archive_dir)
                item.pop('archive_path', None)
        # 当 skip_failed: True 时跳过失败的项目
        elif (step['module_options']['skip_failed'] and 'archive_error' in item.keys() and item['archive_error']):
            logging.debug('跳过 %s (id %s): 上次归档尝试失败，且 skip_failed 设置为 True')
            skipped_count = skipped_count +1
        # 归档匹配 only_tags 的项目
        elif list(set(step['module_options']['only_tags']) & set(item['tags'])):
            logging.info('归档 %s (id %s)', item['url'], item['id'])
            local_archive_path = wget(step, item, local_archive_dir)
            for item2 in items:
                if item2['id'] == item['id']:
                    if local_archive_path is not None:
                        item2['archive_path'] = local_archive_path
                        downloaded_count = downloaded_count + 1
                        item2.pop('archive_error', None)
                    else:
                        item2['archive_error'] = True
                        error_count = error_count + 1
                    break
            write_data_file(step, items)
        else:
            logging.debug('跳过 %s (id %s): 没有匹配 only_tags 的标签', item['url'], item['id'])
            skipped_count = skipped_count + 1
    for visibility in ['public', 'private']:
        dirs_list = []
        if visibility == 'public':
            dirs_list = next(os.walk(step['module_options']['output_directory'] + '/public'))
            ids_in_data = [value['id'] for value in items if value['private'] == False]
        elif visibility == 'private':
            dirs_list = next(os.walk(step['module_options']['output_directory'] + '/private'))
            ids_in_data = [value['id'] for value in items if value['private'] == True]
        else:
            logging.error('visibility 的值无效: %s', visibility)
            sys.exit(1)
        for directory in dirs_list[1]:
            if not any(id == int(directory) for id in ids_in_data):
                if step['module_options']['clean_removed']:
                    # TODO 如果项目从私有更改为公开或相反，本地存档将被删除，但不会再次存档，因为 archive_path 已设置
                    logging.info('找到 id 为 %s 的本地网页存档，但不在数据中。删除 %s', directory, dirs_list[0] + '/' + directory)
                    shutil.rmtree(dirs_list[0] + '/' + directory)
                else:
                    logging.warning('找到 id 为 %s 的本地网页存档，但不在数据中。您可能需要手动删除 %s', dir, dirs_list[0] + '/' + directory)
    logging.info('处理完成。已下载: %s - 已跳过: %s - 错误 %s', downloaded_count, skipped_count, error_count)
    