"""将数据导出为适用于"awesome"列表的单一 markdown 文档
- https://github.com/awesome-selfhosted/awesome-selfhosted
- https://github.com/sindresorhus/awesome
- https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/rJyCEFw.png

--------------------

示例配置文件：

# .hecat.yml
steps:
  - name: 将 YAML 数据导出为单页 markdown
    module: exporters/markdown_singlepage
    module_options:
      source_directory: tests/awesome-selfhosted-data # 源/YAML 数据目录，结构见下文
      output_directory: tests/awesome-selfhosted # 输出目录
      output_file: README.md # 输出 markdown 文件
      markdown_header: markdown/header.md # (可选，默认无) 用作页眉的 markdown 文件路径（相对于 source_directory）
      markdown_footer: markdown/footer.md # (可选，默认无) 用作页脚的 markdown 文件路径（相对于 source_directory）
      back_to_top_url: '#awesome-selfhosted' # (可选，默认 #) 在"返回顶部"链接中使用的 URL/锚点
      exclude_licenses: # (可选，默认无) 不要将具有这些许可证的软件项目写入输出文件（按标识符）
        - '⊘ Proprietary'
        - 'BUSL-1.1'
        - 'CC-BY-NC-4.0'
        - 'CC-BY-NC-SA-3.0'
        - 'CC-BY-ND-3.0'
        - 'Commons-Clause'
        - 'DPL'
        - 'SSPL-1.0'
        - 'DPL'
        - 'Elastic-1.0'
        - 'Elastic-2.0'

  - name: 导出 awesome-selfhosted markdown (非自由)
    module: exporters/markdown_singlepage
    module_options:
      source_directory: tests/awesome-selfhosted-data
      output_directory: tests/awesome-selfhosted
      output_file: non-free.md
      markdown_header: markdown/non-free-header.md
      licenses_file: licenses-nonfree.yml # (可选，默认 licenses.yml) 从中加载许可证的 YAML 文件
      back_to_top_url: '##awesome-selfhosted---non-free-software'
      render_empty_categories: False # (可选，默认 True) 不要渲染包含 0 个项目的类别
      render_category_headers: False # (可选，默认 True) 不要渲染类别标题（描述、相关类别、外部链接...）
      include_licenses: # (默认无) 仅渲染至少匹配其中一个许可证的项目（不能与 exclude_licenses 一起使用）（按标识符）
        - '⊘ Proprietary'
        - 'BUSL-1.1'
        - 'CC-BY-NC-4.0'
        - 'CC-BY-NC-SA-3.0'
        - 'CC-BY-ND-3.0'
        - 'Commons-Clause'
        - 'DPL'
        - 'SSPL-1.0'
        - 'DPL'
        - 'Elastic-1.0'
        - 'Elastic-2.0'

--------------------

输出目录结构：
└── README.md

--------------------

源 YAML 目录结构：
├── markdown
│   ├── header.md # 在最终单页文档中渲染的 markdown 页眉 (markdown_header 模块选项)
│   └── footer.md # 在最终单页文档中渲染的 markdown 页脚 (markdown_footer 模块选项)
├── software
│   ├── mysoftware.yml # 包含软件数据的 .yml 文件
│   ├── someothersoftware.yml
│   └── ...
├── platforms
│   ├── bash.yml # 包含语言/平台数据的 .yml 文件
│   ├── python.yml
│   └── ...
├── tags
│   ├── groupware.yml # 包含标签/类别数据的 .yml 文件
│   ├── enterprise-resource-planning.yml
│   └── ...
└── licenses.yml # 许可证的 YAML 列表 (licenses_file 模块选项)

--------------------

包含软件数据的文件必须按如下格式：

# software/my-awesome-software.yml
# 软件名称
name: "My awesome software"
# 软件项目主页的 URL
website_url: "https://my.awesome.softwar.e"
# 可以下载程序完整源代码的 URL
source_code_url: "https://gitlab.com/awesome/software"
# 软件功能的描述，少于 250 个字符，句子格式
description: "Description of my awesome software."
# 许可证标识符列表（在 licenses_file 中列出）
licenses:
  - Apache-2.0
  - AGPL-3.0
# 语言/平台列表（在 platforms/*.yml 中列出）
platforms:
  - Java
  - Python
  - PHP
  - Nodejs
  - Deb
  - Docker
# 标签（类别）列表（在 tags/*.yml 中列出）
tags:
  - Automation
  - Calendar & Contacts - CalDAV or CardDAV Servers
  - Bookmarks and Link Sharing
  - Pastebins
# (可选，true/false，默认 false) 软件是否依赖于用户控制之外的第三方服务
depends_3rdparty: true
# (可选) 软件的交互式演示链接
demo_url: "https://my.awesome.softwar.e/demo"
# (可选) 软件的客户端/附加组件/插件/应用/机器人...列表链接
related_software_url: "https://my.awesome.softwar.e/apps"
# (可选，由 processors/github_metadata 自动生成) 最后更新/提交日期
updated_at: "20200202T20:20:20Z"
# (可选，由 processors/github_metadata 自动生成) github 项目的星标数
stargazers_count: "999"

--------------------

包含平台/语言的文件必须按如下格式：

# 语言/平台名称
name: Java
# 编程语言或部署平台的一般描述（允许 markdown）
description: "[Java](https://en.wikipedia.org/wiki/Java_(programming_language)) is a high-level, class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible."

--------------------

licenses_file 必须包含一个许可证列表，格式如下：

  # 简短的许可证标识符
- identifier: ZPL-1.2
  # 完整的许可证名称
  name: Zope Public License 1.2
  # 指向完整许可证文本的链接
  url: http://zpl.pub/page/zplv12

--------------------

包含标签/类别的文件必须按如下格式：

# 项目名称
name: Project Management
# 该标签/类别的内容描述（允许 markdown）
description: '[Project management](https://en.wikipedia.org/wiki/Project_management) is the process of leading the work of a team to achieve all project goals within the given constraints.'
# (可选) 相关标签列表，按名称
related_tags:
  - Ticketing
  - Task management & To-do lists
# (可选) 外部链接
external_links:
  - title: awesome-sysadmin/Code Review
    url: https://github.com/awesome-foss/awesome-sysadmin#code-review
# (可选) 应该使用的其他协作列表的 URL
redirect:
  - https://another.awesome.li.st
  - https://gitlab.com/user/awesome-list
"""

import sys
import logging
import ruamel.yaml
from ..utils import to_kebab_case, load_yaml_data, render_markdown_licenses

yaml = ruamel.yaml.YAML(typ='safe')
yaml.indent(sequence=4, offset=2)

def to_markdown_anchor(string):
    """将部分名称转换为 markdown 锚点链接，格式为 [Tag name](#tag-name)"""
    anchor_url = to_kebab_case(string)
    markdown_anchor = '[{}](#{})'.format(string, anchor_url)
    return markdown_anchor

def render_markdown_singlepage_category(step, tag, software_list):
    """为单页 markdown 输出格式渲染一个类别"""
    logging.debug('渲染标签 %s', tag['name'])
    markdown_redirect = ''
    markdown_related_tags = ''
    markdown_description = ''
    markdown_external_links = ''
    items_count = 0

    # 类别标题渲染
    if step['module_options']['render_category_headers']:
        if 'related_tags' in tag and tag['related_tags']:
            markdown_related_tags = '_相关: {}_\n\n'.format(', '.join(
                to_markdown_anchor(related_tag) for related_tag in tag['related_tags']))
        if 'description' in tag and tag['description']:
            markdown_description = tag['description'] + '\n\n'
        if 'redirect' in tag and tag['redirect']:
            markdown_redirect = '**请访问 {}**\n\n'.format(', '.join(
                '[{}]({})'.format(
                    link['title'], link['url']
            ) for link in tag['redirect']))
        if 'external_links' in tag and tag['external_links']:
            markdown_external_links = '_另见: {}_\n\n'.format(', '.join(
                '[{}]({})'.format(
                    link['title'], link['url']
                ) for link in tag['external_links']))
        markdown_category = '### {}{}{}{}{}{}'.format(
            tag['name'] + '\n\n',
            '**[`^        返回顶部        ^`](' + step['module_options']['back_to_top_url'] + ')**\n\n',
            markdown_description,
            markdown_redirect,
            markdown_related_tags,
            markdown_external_links
        )
    else:
        markdown_category = '### {}{}'.format(
            tag['name'] + '\n\n',
            '**[`^        返回顶部        ^`](' + step['module_options']['back_to_top_url'] + ')**\n\n'
        )

    # 软件列表渲染
    for software in software_list:
        if step['module_options']['exclude_licenses']:
            if any(license in software['licenses'] for license in step['module_options']['exclude_licenses']):
                logging.debug("%s 有一个在 exclude_licenses 中列出的许可证，跳过", software['name'])
                continue
        elif step['module_options']['include_licenses']:
            if not any(license in software['licenses'] for license in step['module_options']['include_licenses']):
                logging.debug("%s 不匹配 include_licenses 中列出的任何许可证，跳过", software['name'])
                continue
        if software['tags'][0] == tag['name']:
            markdown_list_item = render_markdown_list_item(software)
            logging.debug('将项目 %s 添加到类别 %s', software['name'], tag['name'])
            markdown_category = markdown_category + markdown_list_item
            items_count = items_count + 1
    if (items_count == 0) and not step['module_options']['render_empty_categories']:
        logging.debug('类别 %s 为空，不渲染它', tag['name'])
        return ''

    return markdown_category + '\n\n'


def render_markdown_list_item(software):
    """将软件项目信息渲染为 markdown 列表项"""
    # 检查可选字段
    if 'demo_url' in software:
        markdown_demo = '[演示]({})'.format(software['demo_url'])
    else:
        markdown_demo = ''
    if not software['source_code_url'] == software['website_url']:
        markdown_source_code = '[源代码]({})'.format(software['source_code_url'])
    else:
        markdown_source_code = ''
    if 'related_software_url' in software:
        markdown_related_software = '[客户端]({})'.format(
            software['related_software_url'])
    else:
        markdown_related_software = ''
    if 'depends_3rdparty' in software and software['depends_3rdparty']:
        markdown_depends_3rdparty = '`⚠` '
    else:
        markdown_depends_3rdparty = ''
    links_list = [markdown_demo, markdown_source_code, markdown_related_software]
    # 从列表中移除空链接
    links = [link for link in links_list if link]
    markdown_links = ' ({})'.format(', '.join(links)) if links else ''
    # 构建 markdown 格式的列表项
    markdown_list_item = '- [{}]({}) {}- {}{} {} {}\n'.format(
        software['name'],
        software['website_url'],
        markdown_depends_3rdparty,
        software['description'],
        markdown_links,
        '`' + '/'.join(software['licenses']) + '`',
        '`' + '/'.join(software['platforms']) + '`'
        )
    return markdown_list_item

def render_markdown_toc(*args):
    """渲染 markdown 格式的目录"""
    markdown = ''
    for i in args:
        markdown += i
    markdown_toc = '\n--------------------\n\n## 目录\n\n'
    # DEBT 因子化
    for line in markdown.split('\n'):
        if line.startswith('## '):
            toc_entry = '- [{}](#{})\n'.format(line[3:], to_kebab_case(line)[3:])
            markdown_toc = markdown_toc + toc_entry
        if line.startswith('### '):
            toc_entry = '  - [{}](#{})\n'.format(line[4:], to_kebab_case(line)[4:])
            markdown_toc = markdown_toc + toc_entry
    markdown_toc = markdown_toc + '\n--------------------'
    return markdown_toc

def render_markdown_singlepage(step):
    """
    渲染所有软件的单页 markdown 列表，按类别分组
    前置/后置页眉/页脚，分类列表和页脚
    一个软件项目只列出一次，在其 'tags:' 列表的第一个项目下
    """
    # pylint: disable=consider-using-with
    tags = load_yaml_data(step['module_options']['source_directory'] + '/tags', sort_key='name')
    software_list = load_yaml_data(step['module_options']['source_directory'] + '/software')
    if 'licenses_file' not in step['module_options']:
        step['module_options']['licenses_file'] = 'licenses.yml'
    licenses = load_yaml_data(step['module_options']['source_directory'] + '/' + step['module_options']['licenses_file'])
    markdown_header = ''
    markdown_footer = ''
    if 'markdown_header' in step['module_options']:
        markdown_header = open(step['module_options']['source_directory'] + '/' + step['module_options']['markdown_header'], 'r', encoding="utf-8").read()
    if 'markdown_footer' in step['module_options']:
        markdown_footer = open(step['module_options']['source_directory'] + '/' + step['module_options']['markdown_footer'], 'r', encoding="utf-8").read()
    markdown_software_list = '## 软件\n\n'
    if ('exclude_licenses' in step['module_options']) and ('include_licenses' in step['module_options']):
        logging.error('模块选项 exclude_licenses 和 include_licenses 不能一起使用。')
        sys.exit(1)
    if 'exclude_licenses' not in step['module_options']:
        step['module_options']['exclude_licenses'] = []
    if 'include_licenses' not in step['module_options']:
        step['module_options']['include_licenses'] = []
    if 'back_to_top_url' not in step['module_options']:
        step['module_options']['back_to_top_url'] = '#'
    if 'render_empty_categories' not in step['module_options']:
        step['module_options']['render_empty_categories'] = True
    if 'render_category_headers' not in step['module_options']:
        step['module_options']['render_category_headers'] = True
    for tag in tags:
        markdown_category = render_markdown_singlepage_category(step, tag, software_list)
        markdown_software_list = markdown_software_list + markdown_category
    markdown_licenses = render_markdown_licenses(step, licenses, back_to_top_url=step['module_options']['back_to_top_url'])
    markdown_toc_section = render_markdown_toc(
        markdown_header,
        markdown_software_list,
        markdown_licenses,
        markdown_footer)
    markdown = '{}{}\n\n{}{}\n{}'.format(
        markdown_header, markdown_toc_section, markdown_software_list, markdown_licenses, markdown_footer)
    with open(step['module_options']['output_directory'] + '/' + step['module_options']['output_file'], 'w+', encoding="utf-8") as outfile:
        outfile.write(markdown)
