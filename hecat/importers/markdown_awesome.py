"""从 awesome-selfhosted markdown 格式导入数据
- https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/E4ra3V8.png

# hecat.yml
steps:
  - name: 导入
    module: importers/markdown_awesome
    module_options:
      source_file: tests/awesome-selfhosted/README.md
      output_directory: tests/awesome-selfhosted-data
      output_licenses_file: licenses.yml # 可选，默认 licenses.yml
      overwrite_tags: False # 可选，默认 False

源目录结构：
└── README.md

输出目录结构：
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
└── licenses.yml # 许可证的 yaml 列表

除了列表项格式
(https://github.com/awesome-selfhosted/awesome-selfhosted/blob/master/.github/PULL_REQUEST_TEMPLATE.md)，
导入器对原始 markdown 文件有一些假设：
- 所有三级（`###`）标题/部分包含实际的列表数据/项，其他部分必须使用二级标题
- 许可证列表在 `## List of Licenses` 部分中提供

软件/平台/标签的输出格式在 exporters/markdown_singlepage.py 中描述
"""

import os
import sys
import logging
import re
import ruamel.yaml
from ..utils import list_files, to_kebab_case

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=4, offset=2)
yaml.width = 99999

def load_markdown_list_sections(source_file):
    """返回原始 markdown 列表部分，作为字典列表：
       title: 部分标题
       text: 完整部分文本
    """
    with open(source_file, 'r', encoding="utf-8") as src_file:
        src = src_file.read()
        sections = []
        for section in src.split('### '):
            title = section.partition('\n')[0]
            sections.append({ 'title': title, 'text': section })
        # 移除第一个 ### 之前的所有内容
        sections.pop(0)
        # 只保留最后一个部分中 ##（下一个二级部分的开始）之前的内容
        sections[-1]['text'] = sections[-1]['text'].split('## ')[0]
    return sections

def import_software(section, step, errors):
    """从 markdown 部分/类别中导入所有列表项到软件 yaml 定义/文件"""
    entries = re.findall("^- .*", section['text'], re.MULTILINE)
    for line in entries:
        logging.debug('从行导入软件: %s', line)
        # 匹配如: - [名称](网址) - 描述。([源码](源码链接)) `许可证` `语言`
        # matches = re.match(r"\- \[(?P<name>.*)\]\((?P<website_url>[^\)]+)\) (?P<depends_3rdparty>`⚠` )?- (?P<description>.*\.) ((?P<links>.*)\)\) )?`(?P<license>.*)` `(?P<language>.*)`", line) # pylint: disable=line-too-long
        matches = re.match(
            r"\- \[(?P<name>[^\]]+)\]\((?P<website_url>[^\)]+)\) ?(?P<depends_3rdparty>`⚠` )?- (?P<description>.*?)(?:。|\.)?(?:\s*\(\[(?P<source_code_label>源码|Source Code)\]\((?P<source_code_url>[^\)]+)\)\))? `(?P<license>[^`]+)` `(?P<language>[^`]+)`",
            line)
        entry = {}
        try:
            entry['name'] = matches.group('name')
            entry['website_url'] = matches.group('website_url')
            entry['description'] = matches.group('description').strip()
            entry['licenses'] = matches.group('license').split('/')
            entry['platforms'] = matches.group('language').split('/')
            entry['tags'] = [section['title']]
            # 源码链接优先用 source_code_url，否则 fallback 到 website_url
            # if matches.group('source_code_url'):
            # entry['source_code_url'] = matches.group('source_code_url')
            # else:
            # entry['source_code_url'] = entry['website_url']
        except AttributeError:
            error_msg = '条目中缺少必填字段: {}'.format(line)
            logging.error(error_msg)
            errors.append(error_msg)
            continue
        if matches.group('links') is not None:
            source_code_url_match = re.match(r".*\[Source Code\]\(([^\)]+).*", matches.group('links'))
            if source_code_url_match is not None:
                entry['source_code_url'] = source_code_url_match.group(1)
            else:
                entry['source_code_url'] = entry['website_url']
            demo_url_match = re.match(r".*\[Demo\]\(([^\)]+).*", matches.group('links'))
            if demo_url_match is not None:
                entry['demo_url'] = demo_url_match.group(1)
            related_software_url_match = re.match(r".*\[Clients\]\(([^\)]+).*", matches.group('links'))
            if related_software_url_match is not None:
                entry['related_software_url'] = related_software_url_match.group(1)
        else:
            entry['source_code_url'] = entry['website_url']
        if matches.group('depends_3rdparty'):
            entry['depends_3rdparty'] = True

        dest_file = '{}/{}'.format(
            step['module_options']['output_directory'] + '/software',
            to_kebab_case(matches.group('name')) + '.yml')
        if os.path.exists(dest_file):
            logging.debug('覆盖目标文件 %s', dest_file)
        while True:
            try:
                with open(dest_file, 'w+', encoding="utf-8") as yaml_file:
                    logging.debug('部分 %s: 写入文件 %s', section['title'], dest_file)
                    yaml.dump(entry, yaml_file)
                    break
            except FileNotFoundError:
                os.mkdir(step['module_options']['output_directory'] + '/software')

# DEBT 提取外部链接、相关标签、重定向的因子化
def extract_related_tags(section):
    """从 markdown 部分提取 'Related:' 标签"""
    related_tags = []
    related_markdown = re.findall("^_Related:.*_", section['text'], re.MULTILINE)
    if related_markdown:
        matches = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", related_markdown[0])
        for match in matches:
            related_tags.append(match[0])
    return related_tags

def extract_redirect(section):
    """从 markdown 中提取 'Please visit' 链接标题/URL"""
    redirect = []
    redirect_markdown = re.findall(r'^\*\*Please visit.*\*\*', section['text'], re.MULTILINE)
    if redirect_markdown:
        matches = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", redirect_markdown[0])
        for match in matches:
            redirect.append({ 'title': match[0], 'url': match[1]})
    return redirect

def extract_external_links(section):
    """从 markdown 部分提取 'See also:' 链接标题/URL"""
    external_links = []
    external_links_markdown = re.findall("^_See also.*_", section['text'], re.MULTILINE)
    if external_links_markdown:
        matches = re.findall(r"\[([^\]]*)\]\(([^\)]*)\)", external_links_markdown[0])
        for match in matches:
            external_links.append({ 'title': match[0], 'url': match[1]})
    return external_links

def extract_description(section):
    """从 markdown 部分提取部分描述"""
    description = ''
    description_markdown = re.findall(r'^(?![#\*_\-\n]).*', section['text'], re.MULTILINE)
    if description_markdown:
        if len(description_markdown) in [1, 2]:
            logging.warning("%s 没有描述", section['title'])
        if len(description_markdown) == 3:
            description = description_markdown[1]
        else:
            logging.warning("%s 有超过一行描述。只保留第一行", section['title'])
            description = description_markdown[1]
    return description

def import_tag(section, step):
    """根据源 markdown 部分/类别创建标签/类别 yaml 文件"""
    if 'overwrite_tags' not in step['module_options']:
        step['module_options']['overwrite_tags'] = False
    dest_file = '{}/{}'.format(
        step['module_options']['output_directory'] + '/tags', to_kebab_case(section['title']) + '.yml')
    if os.path.exists(dest_file):
        if not step['module_options']['overwrite_tags']:
            logging.debug('文件 %s 已存在，不覆盖', dest_file)
            return
        logging.debug('覆盖标签在 %s', dest_file)
    related_tags = extract_related_tags(section)
    redirect = extract_redirect(section)
    description = extract_description(section)
    external_links = extract_external_links(section)
    while True:
        try:
            with open(dest_file, 'w+', encoding="utf-8") as yaml_file:
                logging.debug('部分 %s: 写入文件 %s', section['title'], dest_file)
                output_dict = {
                    'name': section['title'],
                    'description': description,
                }
                if external_links:
                    output_dict['external_links'] = external_links
                if redirect:
                    output_dict['redirect'] = redirect
                if related_tags:
                    output_dict['related_tags'] = related_tags
                yaml.dump(output_dict, yaml_file)
                break
        except FileNotFoundError:
            os.mkdir(step['module_options']['output_directory'] + '/tags')

def import_platforms(yaml_software_files, step):
    """从所有软件/YAML 文件构建语言/平台列表，
    创建相应的 platform/*.yml 文件"""
    platforms = []
    for file in yaml_software_files:
        with open(step['module_options']['output_directory'] + '/software/' + file, 'r', encoding="utf-8") as file:
            data = yaml.load(file)
            platforms = platforms + data['platforms']
    platforms = list(set(platforms))
    for platform in platforms:
        dest_file = '{}/{}'.format(
            step['module_options']['output_directory'] + '/platforms', to_kebab_case(platform) + '.yml')
        if os.path.exists(dest_file):
            logging.debug('覆盖目标文件 %s', dest_file)
        with open(dest_file, 'w+', encoding="utf-8") as yaml_file:
            logging.debug('写入文件 %s', dest_file)
            yaml_file.write('name: {}\ndescription: ""'.format(platform))

def import_licenses(step):
    """从 markdown 文件的 List of Licenses 部分构建 YAML 许可证列表"""
    yaml_licenses = ''
    with open(step['module_options']['source_file'], 'r', encoding="utf-8") as markdown:
        data = markdown.read()
        licenses_section = data.split('## 许可证清单')[1].split('## ')[0]
        entries = re.findall("^- .*", licenses_section, re.MULTILINE)
        # pylint: disable=line-too-long
        for line in entries:
            matches = re.match(r"\- \`(?P<identifier>.*)\` - (\[(?P<name>.*)\]\((?P<url>.*)\))?", line)
            yaml_identifier = '- identifier: {}\n'.format(matches.group('identifier'))
            yaml_name = ('  name: {}\n'.format(matches.group('name')) if (matches.group('name')) is not None else '')
            yaml_url = ('  url: {}\n'.format(matches.group('url')) if (matches.group('url')) is not None else '')
            yaml_list_item = '{}{}{}'.format(yaml_identifier, yaml_name, yaml_url)
            yaml_licenses = yaml_licenses + '\n' + yaml_list_item
    if 'output_licenses_file' not in step['module_options']:
        step['module_options']['output_licenses_file'] = 'licenses.yml'
    dest_file = step['module_options']['output_directory'] + '/' + step['module_options']['output_licenses_file']
    with open(dest_file, 'w+', encoding="utf-8") as yaml_file:
        logging.debug('写入文件 %s', dest_file)
        yaml_file.write(yaml_licenses)

def import_markdown_awesome(step):
    """从“awesome”格式的 markdown 列表导入数据
    原始列表部分必须是三级标题（###）
    """
    errors = []
    sections = load_markdown_list_sections(step['module_options']['source_file'])
    for section in sections:
        import_software(section, step, errors)
        import_tag(section, step)
    if errors:
        logging.error("处理过程中出现错误")
        sys.exit(1)
    yaml_software_files = list_files(step['module_options']['output_directory'] + '/software')
    import_platforms(yaml_software_files, step)
    import_licenses(step)
    