"""github_metadata 处理器
从 GitHub API 获取项目/仓库元数据并向 YAML 数据添加一些字段（`updated_at`、`stargazers_count`、`archived`）。

# hecat.yml
steps:
  - step: process
    module: processors/github_metadata
    module_options:
      source_directory: tests/awesome-selfhosted-data # 包含 YAML 数据和 software 子目录的目录
      gh_metadata_only_missing: False # (默认 False) 仅收集缺少 stargazers_count、updated_at、archived 之一的软件条目的元数据
      sleep_time: 3.7 # (默认 0) 在每次请求 Github API 之前睡眠此时间

source_directory: 数据文件所在的目录路径。目录结构：
├── software
│   ├── mysoftware.yml # 包含软件数据的 .yml 文件
│   ├── someothersoftware.yml
│   └── ...
├── platforms
├── tags
└── ...

必须在 `GITHUB_TOKEN` 环境变量中定义一个 Github 访问令牌（无需特权）：
$ GITHUB_TOKEN=AAAbbbCCCdd... hecat -c .hecat.yml
在 Github Actions 中，每个作业都会自动创建一个令牌。要使其在环境中可用，请使用以下工作流配置：
# .github/workflows/ci.yml
env:
  GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}

使用 GITHUB_TOKEN 时，API 速率限制为每小时每个仓库 1,000 个请求 [[1]](https://docs.github.com/en/rest/overview/resources-in-the-rest-api?apiVersion=2022-11-28#rate-limits-for-requests-from-github-actions)
注意，每次调用 get_gh_metadata() 会产生 2 个 API 请求（一个用于仓库/星标数，一个用于最新提交日期）
"""

import sys
import logging
import re
import os
import time
from datetime import datetime
import ruamel.yaml
import github
from ..utils import load_yaml_data, to_kebab_case

yaml = ruamel.yaml.YAML(typ='rt')
yaml.indent(sequence=4, offset=2)
yaml.width = 99999

class DummyGhMetadata(dict):
    """当从 github API 获取元数据失败时将返回的虚拟元数据对象"""
    def __init__(self):
        self.stargazers_count = 0
        self.archived = False

def get_gh_metadata(step, github_url, g, errors):
    """从 Github API 获取 github 项目元数据"""
    if 'sleep_time' in step['module_options']:
        time.sleep(step['module_options']['sleep_time'])
    project = re.sub('https://github.com/', '', github_url)
    project = re.sub('/$', '', project)
    try:
        gh_metadata = g.get_repo(project)
        latest_commit_date = gh_metadata.get_commits()[0].commit.committer.date
    except github.GithubException as github_error:
        error_msg = '{} : {}'.format(github_url, github_error)
        logging.error(error_msg)
        errors.append(error_msg)
        gh_metadata = DummyGhMetadata()
        latest_commit_date = datetime.strptime('1970-01-01', '%Y-%m-%d')
    return gh_metadata, latest_commit_date

def write_software_yaml(step, software):
    """将软件数据写入 yaml 文件"""
    dest_file = '{}/{}'.format(
                               step['module_options']['source_directory'] + '/software',
                               to_kebab_case(software['name']) + '.yml')
    logging.debug('写入文件 %s', dest_file)
    with open(dest_file, 'w+', encoding="utf-8") as yaml_file:
        yaml.dump(software, yaml_file)

def add_github_metadata(step):
    """收集 github 项目数据并将其添加到源 YAML 文件"""
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    g = github.Github(GITHUB_TOKEN)
    errors = []
    software_list = load_yaml_data(step['module_options']['source_directory'] + '/software')
    logging.info('从 Github API 更新软件数据')
    for software in software_list:
        github_url = ''
        if 'source_code_url' in software:
            if re.search(r'^https://github.com/[\w\.\-]+/[\w\.\-]+/?$', software['source_code_url']):
                github_url = software['source_code_url']
        elif 'website_url' in software:
            if re.search(r'^https://github.com/[\w\.\-]+/[\w\.\-]+/?$', software['website_url']):
                github_url = software['website_url']
        if github_url:
            logging.debug('%s 是一个 github 项目 URL', github_url)
            if 'gh_metadata_only_missing' in step['module_options'].keys() and step['module_options']['gh_metadata_only_missing']:
                if ('stargazers_count' not in software) or ('updated_at' not in software) or ('archived' not in software):
                    logging.info('缺少 %s 的元数据，从 Github API 收集', software['name'])
                    gh_metadata, latest_commit_date = get_gh_metadata(step, github_url, g, errors)
                    software['stargazers_count'] = int(gh_metadata.stargazers_count)
                    software['updated_at'] = datetime.strftime(latest_commit_date, "%Y-%m-%d")
                    software['archived'] = bool(gh_metadata.archived)
                    write_software_yaml(step, software)
                else:
                    logging.debug('所有元数据已存在，跳过 %s', github_url)
            else:
                logging.info('从 Github API 收集 %s 的元数据', github_url)
                gh_metadata, latest_commit_date = get_gh_metadata(step, github_url, g, errors)
                software['stargazers_count'] = gh_metadata.stargazers_count
                software['updated_at'] = datetime.strftime(latest_commit_date, "%Y-%m-%d")
                software['archived'] = gh_metadata.archived
                write_software_yaml(step, software)
    if errors:
        logging.error("处理过程中出现错误")
        print('\n'.join(errors))
        sys.exit(1)
        