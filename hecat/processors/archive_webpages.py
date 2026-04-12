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
      data_file: tests/shaarli.yml # path to the YAML data file
      only_tags: ['doc'] # only download items tagged with any of these tags
      exclude_tags: ['nodl'] # (default []), don't download items tagged with any of these tags
      exclude_regex: # (default []) don't archive URLs matching these regular expressions
        - '^https://[a-z]\.wikipedia.org/wiki/.*$' # don't archive wikipedia pages, supposing you have a local copy of wikipedia dumps from https://dumps.wikimedia.org/
      output_directory: 'tests/webpages' # path to the output directory for archived pages
      skip_already_archived: True # (default True) skip processing when item already has a 'archive_path': key
      clean_removed: True # (default False) remove existing archived pages which do not match any id in the data file
      clean_excluded: True # (default False) remove existing archived pages matching exclude_regex
      skip_failed: False # (default False) don't attempt to archive items for which the previous archival attempt failed (archive_error: True)
      wget_errors_are_fatal: True # (default False) exit immediately if a wget download error occurs

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

# Constants
DEFAULT_WGET_TIMEOUT = 30
DEFAULT_WGET_TRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=2, offset=0)
yaml.width = 99999

def wget(step, item, wget_output_directory):
    """archive a webpage with wget, return the local path of the archived file"""
    os.makedirs(wget_output_directory, exist_ok=True)

    wget_bin = shutil.which('wget')
    if not wget_bin:
        raise FileNotFoundError("wget not found in PATH")

    wget_process = subprocess.Popen([wget_bin,
                                     '--continue',
                                     '--span-hosts',
                                     '--adjust-extension',
                                     '--timestamping',
                                     '--convert-links',
                                     '--page-requisites',
                                     '--no-verbose',
                                     f'--timeout={DEFAULT_WGET_TIMEOUT}',
                                     f'--tries={DEFAULT_WGET_TRIES}',
                                     '-e', 'robots=off',
                                     f'--user-agent={USER_AGENT}',
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
        logging.error('error while archiving %s', item['url'])
        if step['module_options'].get('wget_errors_are_fatal', False):
            logging.error('wget error encountered and wget_errors_are_fatal is True. Exiting.')
            sys.exit(1)
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

def initialize_output_directories(output_directory):
    """Create public and private subdirectories in the output directory"""
    for visibility in ['/public', '/private']:
        os.makedirs(output_directory + visibility, exist_ok=True)


def set_default_options(module_options):
    """Set default values for module options if not present"""
    module_options.setdefault('clean_removed', False)
    module_options.setdefault('skip_failed', False)
    module_options.setdefault('only_tags', [])
    module_options.setdefault('wget_errors_are_fatal', False)


def get_local_archive_dir(output_directory, item):
    """Get the local archive directory path for an item based on its privacy setting"""
    visibility = 'private' if item['private'] else 'public'
    return f"{output_directory}/{visibility}/{item['id']}"


def is_item_excluded(item, module_options):
    """Check if item should be excluded based on tags or regex patterns
    Returns: (is_excluded: bool, excluded_by_tags: bool, excluded_by_regex: bool)
    """
    excluded_by_tags = (module_options.get('exclude_tags') and
                       any(tag in item['tags'] for tag in module_options['exclude_tags']))
    excluded_by_regex = (module_options.get('exclude_regex') and
                        any(re.search(regex, item['url']) for regex in module_options['exclude_regex']))
    return (excluded_by_tags or excluded_by_regex, excluded_by_tags, excluded_by_regex)


def handle_excluded_item(item, local_archive_dir, excluded_by_tags, excluded_by_regex, clean_excluded):
    """Handle an excluded item: clean up if needed and log the reason"""
    if clean_excluded:
        if os.path.isdir(local_archive_dir):
            if excluded_by_tags:
                logging.info('removing local archive directory %s for URL %s (one or more tags match exclude_tags)', local_archive_dir, item['url'])
            else:
                logging.info('removing local archive directory %s for URL %s (URL matches exclude_regex)', local_archive_dir, item['url'])
            shutil.rmtree(local_archive_dir)
        item.pop('archive_path', None)

    if excluded_by_tags:
        logging.debug('skipping %s (id %s): one or more tags are present in exclude_tags', item['url'], item['id'])
    else:
        logging.debug('skipping %s (id %s): URL matches exclude_regex', item['url'], item['id'])


def should_process_item(item, module_options):
    """Determine if an item should be processed for archiving
    Returns: (should_process: bool, reason: str)
    Reasons: 'process', 'already_archived', 'failed', 'no_matching_tags'
    """
    # skip already archived items when skip_already_archived: True
    if (module_options.get('skip_already_archived', True) and
        item.get('archive_path') is not None):
        return (False, 'already_archived')

    # skip failed items when skip_failed: True
    if (module_options.get('skip_failed', False) and
        item.get('archive_error', False)):
        return (False, 'failed')

    # archive items matching only_tags (ANY tag must be present)
    only_tags = module_options.get('only_tags', [])
    if set(only_tags).intersection(set(item['tags'])):
        return (True, 'process')

    return (False, 'no_matching_tags')


def cleanup_removed_archives(output_directory, items, clean_removed):
    """Remove archived directories for items that no longer exist in the data file"""
    for visibility in ['public', 'private']:
        dirs_list = next(os.walk(f"{output_directory}/{visibility}"))
        ids_in_data = [value['id'] for value in items if value['private'] == (visibility == 'private')]

        for directory in dirs_list[1]:
            if not any(id == int(directory) for id in ids_in_data):
                archive_path = f"{dirs_list[0]}/{directory}"
                if clean_removed:
                    # TODO if an item was changed from private to public or the other way around, the local archive will be deleted, but it will not be archived again since archive_path is already set
                    logging.info('local webpage archive found with id %s, but not in data. Deleting %s', directory, archive_path)
                    shutil.rmtree(archive_path)
                else:
                    logging.warning('local webpage archive found with id %s, but not in data. You may want to delete %s manually', directory, archive_path)


def process_single_item(step, item, local_archive_dir, items):
    """Archive a single item and update its metadata
    Returns: (success: bool, error_occurred: bool)
    """
    logging.info('archiving %s (id %s)', item['url'], item['id'])
    local_archive_path = wget(step, item, local_archive_dir)

    if local_archive_path is not None:
        item['archive_path'] = local_archive_path
        item.pop('archive_error', None)
        success, error = True, False
    else:
        item['archive_error'] = True
        success, error = False, True

    write_data_file(step, items)  # Checkpoint after processing
    return (success, error)


def archive_webpages(step):
    """archive webpages linked from each item's 'url', if one of their tags matches one of step['only_tags'],
    write path to local archive to a new key 'archive_path' in the original data file for each downloaded item
    """
    # Validate required options
    required_options = ['data_file', 'output_directory']
    for opt in required_options:
        if opt not in step['module_options']:
            raise ValueError(f"Missing required module option: {opt}")

    downloaded_count = 0
    skipped_count = 0
    error_count = 0

    initialize_output_directories(step['module_options']['output_directory'])

    items = load_yaml_data(step['module_options']['data_file'])

    set_default_options(step['module_options'])

    for item in items:
        local_archive_dir = get_local_archive_dir(step['module_options']['output_directory'], item)

        # Check if item should be excluded (tags or regex)
        is_excluded, excluded_by_tags, excluded_by_regex = is_item_excluded(item, step['module_options'])

        # Clean excluded items if clean_excluded is True
        if is_excluded:
            handle_excluded_item(item, local_archive_dir, excluded_by_tags, excluded_by_regex,
                               step['module_options'].get('clean_excluded', False))
            skipped_count += 1
        else:
            should_process, reason = should_process_item(item, step['module_options'])

            if should_process:
                success, error = process_single_item(step, item, local_archive_dir, items)
                if success:
                    downloaded_count += 1
                if error:
                    error_count += 1
            else:
                if reason == 'already_archived':
                    logging.debug('skipping %s (id %s): already archived', item['url'], item['id'])
                elif reason == 'failed':
                    logging.debug('skipping %s (id %s): the previous archival attempt failed, and skip_failed is set to True', item['url'], item['id'])
                elif reason == 'no_matching_tags':
                    logging.debug('skipping %s (id %s): no tags matching only_tags', item['url'], item['id'])
                skipped_count += 1

    cleanup_removed_archives(step['module_options']['output_directory'], items,
                            step['module_options']['clean_removed'])

    logging.info('processing complete. Downloaded: %s - Skipped: %s - Errors %s', downloaded_count, skipped_count, error_count)
