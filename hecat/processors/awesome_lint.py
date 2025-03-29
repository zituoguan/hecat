"""awesome_lint 处理器
根据 awesome-selfhosted 指南检查条目
https://github.com/awesome-selfhosted/awesome-selfhosted

# .hecat.yml
steps:
  - name: lint
    module: processors/awesome_lint
    module_options:
      source_directory: tests/awesome-selfhosted-data
      items_in_redirect_fatal: False # (可选，默认 True) 当条目在其 `tags` 列表中包含设置了 'redirect' 的标签时失败
      last_updated_error_days: 3650 # (可选，默认 3650) 对于超过这个天数未更新的项目，引发错误消息
      last_updated_warn_days: 365 # (可选，默认 365) 对于超过这个天数未更新的项目，引发警告消息
      last_updated_info_days: 186 # (可选，默认 186) 对于超过这个天数未更新的项目，引发信息消息
      licenses_files: # (可选，默认 ['licenses.yml']) 包含许可证列表的文件路径
        - licenses.yml
        - licenses-nonfree.yml
      last_updated_skip: # (可选，默认 []) 不应产生最后更新日期检查错误/警告的项目列表 (source_code_url)
        - https://github.com/tomershvueli/homepage # 简单/无需维护 https://github.com/awesome-selfhosted/awesome-selfhosted-data/pull/242
        - https://github.com/abrenaut/posio # 简单/无需维护
        - https://github.com/knrdl/bicimon # 简单/无需维护
        - https://github.com/Kshitij-Banerjee/Cubiks-2048 # 简单/无需维护
      platforms_required_fields: ['description'] # (可选，默认 ['description']) 所有平台必须定义的属性


source_directory: 数据所在目录的路径。目录结构：
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
├── licenses.yml # 许可证的 yaml 列表
└── licenses-nonfree.yml # 许可证的 yaml 列表
"""

import os
import re
import logging
import sys
from datetime import datetime, timedelta
from ..utils import load_yaml_data, to_kebab_case

SOFTWARE_REQUIRED_FIELDS = ['description', 'website_url', 'source_code_url', 'licenses', 'tags']
SOFTWARE_REQUIRED_LISTS = ['licenses', 'tags']
TAGS_REQUIRED_FIELDS = ['description']
LICENSES_REQUIRED_FIELDS= ['identifier', 'name', 'url']

def check_required_fields(item, errors, required_fields=[], required_lists=[], severity=logging.error):
    """检查键（required_fields）是否已定义且长度不为零
       检查 required_lists 中的每个项目是否已定义且长度不为零
    """
    for key in required_fields:
        try:
            assert len(item[key]) > 0
        except KeyError:
            message = "{}: {} 未定义".format(item['name'], key)
            log_exception(message, errors, severity)
        except AssertionError:
            message = "{}: {} 为空".format(item['name'], key)
            log_exception(message, errors, severity)
    for key in required_lists:
        try:
            for value in item[key]:
                try:
                    assert len(value) > 0
                except AssertionError:
                    message = "{}: {} 列表包含空字符串".format(item['name'], key)
                    log_exception(message, errors, severity)
        except KeyError:
            message = "{}: {} 未定义".format(item['name'], key)
            log_exception(message, errors, severity)


def log_exception(message, errors, severity=logging.error):
    """记录警告或错误消息，如果 severity=logging.error，则将错误添加到全局错误列表中"""
    severity(message)
    if severity == logging.error:
        errors.append(message)


def check_description_syntax(software, errors):
    """检查描述是否短于 250 个字符，以大写字母开头并以句点结尾"""
    try:
        assert len(software['description']) <= 250
    except AssertionError:
        message = "{}: 描述长度超过 250 个字符".format(software['name'])
        log_exception(message, errors)
    # 不阻塞/只引发警告，因为描述可能出于正当理由不以大写字母开头（参见 üwave, groceri.es...）
    try:
        assert software['description'][0].isupper()
    except AssertionError:
        message = ("{}: 描述不以大写字母开头").format(software['name'])
        log_exception(message, errors, severity=logging.warning)
    try:
        assert software['description'].endswith('.')
    except AssertionError:
        message = ("{}: 描述不以句点结尾").format(software['name'])
        log_exception(message, errors, severity=logging.warning)

def check_attribute_in_list(item, attribute_name, key, attributes_list, errors):
    """检查软件/标签项目的所有许可证/标签/平台/相关标签是否列在主许可证/标签/平台列表中。
    :param dict software: 包含要检查的数据的对象（例如软件项目或标签项目）
    :param str attribute_name: 属性名称（例如 'licenses' 或 'tags'）
    :param str key: 要根据主列表检查的键名称（例如 'identifier' 或 'name'）
    :param list attributes_list: 要根据其检查每个键/值对的值的主列表（例如 licenses_list 或 tags_list）
    :param list errors: 以前错误的列表
    """
    if attribute_name in item:
        for attr in list(item[attribute_name]):
            try:
                assert any(item2[key] == attr for item2 in attributes_list)
            except AssertionError:
                message = "{}: {} {} 未列在主 {} 列表中".format(item['name'], attribute_name, attr, attribute_name)
                log_exception(message, errors)

def check_tag_has_at_least_items(tag, software_list, tags_with_redirect, errors, min_items=3):
    """检查一个标签是否至少有 N 个软件项目与之关联"""
    tag_items_count = 0
    for software in software_list:
        if tag['name'] in software['tags']:
            tag_items_count += 1
    try:
        assert tag_items_count >= min_items
        logging.debug('%s 个项目标记为 %s', tag_items_count, tag['name'])
    except AssertionError:
        if tag['name'] in tags_with_redirect and tag_items_count == 0:
            logging.debug('0 个项目标记为 %s，但此标签已设置 redirect 属性', tag['name'])
        else:
            message = "{} 个项目标记为 {}，每个标签必须至少关联 {} 个项目".format(tag_items_count, tag['name'], min_items)
            log_exception(message, errors)

def check_redirect_sections_empty(step, software, tags_with_redirect, errors):
    """检查标签列表中的任何标签是否不匹配已设置重定向的标签"""
    for tag in software['tags']:
        try:
            assert tag not in tags_with_redirect
        except AssertionError:
            message = "{}: 标签 {} 指向一个重定向到另一个列表的标签。".format(software['name'], tag)
            if 'items_in_redirect_fatal' in step['module_options'].keys() and not step['module_options']['items_in_redirect_fatal']:
                log_exception(message, errors, severity=logging.warning)
            else:
                log_exception(message, errors)


def check_external_link_syntax(software, errors):
    """检查外部链接的格式是否为 [text](url)"""
    try:
        for link in software['external_links']:
            try:
                assert re.match(r'^\[.*\]\(.*\)$', link)
            except AssertionError:
                message = ("{}: 外部链接 {} 的语法不正确").format(software['name'], link)
                log_exception(message, errors)
    except KeyError:
        pass


def check_not_archived(software, errors):
    """检查软件项目是否未标记为 archived: True"""
    try:
        assert not software['archived']
    except AssertionError:
        message = ("{}: 该项目已归档").format(software['name'])
        log_exception(message, errors)
    except KeyError:
        pass

def check_last_updated(software, step, errors):
    """检查项目的最后更新日期，如果早于配置的阈值，则发出信息/警告/错误消息"""
    if 'updated_at' in software:
        last_update_time = datetime.strptime(software['updated_at'], "%Y-%m-%d")
        time_since_last_update = last_update_time - datetime.now()
        if software['source_code_url'] in step['module_options']['last_updated_skip']:
            logging.info('%s: 根据配置（last_updated_skip）跳过最后更新时间检查（%s）', software['name'], time_since_last_update)
        elif last_update_time < datetime.now() - timedelta(days=step['module_options']['last_updated_error_days']):
            message = '{}: 最后更新于 {} 之前，早于 {} 天'.format(software['name'], time_since_last_update, step['module_options']['last_updated_error_days'])
            log_exception(message, errors, severity=logging.error)
        elif last_update_time < datetime.now() - timedelta(days=step['module_options']['last_updated_warn_days']):
            logging.warning('%s: 最后更新于 %s 之前，早于 %s 天', software['name'], time_since_last_update, step['module_options']['last_updated_warn_days'])
        elif last_update_time < datetime.now() - timedelta(days=step['module_options']['last_updated_info_days']):
            logging.info('%s: 最后更新于 %s 之前，早于 %s 天', software['name'], time_since_last_update, step['module_options']['last_updated_info_days'])
        else:
            logging.debug('%s: 最后更新于 %s 之前', software['name'], time_since_last_update)

def check_boolean_attributes(software, errors):
    """检查 depends_3rdparty 属性是否为布尔值"""
    if 'depends_3rdparty' in software:
        if not type(software['depends_3rdparty']) == bool:
            message = '{}: depends_3rdparty 必须是有效的布尔值（true/false/True/False），得到的是 "{}"'.format(software['name'], software['depends_3rdparty'])
            log_exception(message, errors, severity=logging.error)

def check_filename_is_kebab_case_software_name(filename, single_yaml_data, errors):
    """检查 yaml 的文件名是否与该文件内部 name 属性的 kebab-case 版本匹配"""
    if not filename == to_kebab_case(single_yaml_data['name']) + '.yml':
        message = '{}: 文件应命名为 {}'.format(filename, to_kebab_case(single_yaml_data['name'] + '.yml'))
        log_exception(message, errors, severity=logging.error)

def awesome_lint(step):
    """根据格式指南检查所有软件条目"""
    logging.info('根据格式指南检查软件条目/标签。')
    software_list = load_yaml_data(step['module_options']['source_directory'] + '/software')
    if 'last_updated_info_days' not in step['module_options']:
        step['module_options']['last_updated_info_days'] = 186
    if 'last_updated_warn_days' not in step['module_options']:
        step['module_options']['last_updated_warn_days'] = 365
    if 'last_updated_error_days' not in step['module_options']:
        step['module_options']['last_updated_error_days'] = 3650
    if 'licenses_files' not in step['module_options']:
        step['module_options']['licenses_files'] = ['/licenses.yml']
    if  'last_updated_skip' not in step['module_options']:
        step['module_options']['last_updated_skip'] = []
    if 'platforms_required_fields' not in step['module_options']:
        step['module_options']['platforms_required_fields'] = ['description']
    licenses_list = []
    for filename in step['module_options']['licenses_files']:
        licenses_list = licenses_list + load_yaml_data(step['module_options']['source_directory'] + '/' + filename)
    tags_list = load_yaml_data(step['module_options']['source_directory'] + '/tags')
    tags_with_redirect = []
    for tag in tags_list:
        if 'redirect' in tag and tag['redirect']:
            tags_with_redirect.append(tag['name'])
    platforms_list = load_yaml_data(step['module_options']['source_directory'] + '/platforms')
    errors = []
    for tag in tags_list:
        check_attribute_in_list(tag, 'related_tags', 'name', tags_list, errors)
        check_required_fields(tag, errors, required_fields=TAGS_REQUIRED_FIELDS, severity=logging.warning)
        check_tag_has_at_least_items(tag, software_list, tags_with_redirect, errors, min_items=3)
    for platform in platforms_list:
        check_required_fields(platform, errors, required_fields=step['module_options']['platforms_required_fields'])
    for software in software_list:
        check_required_fields(software, errors, required_fields=SOFTWARE_REQUIRED_FIELDS, required_lists=SOFTWARE_REQUIRED_LISTS)
        check_description_syntax(software, errors)
        check_attribute_in_list(software, 'licenses', 'identifier', licenses_list, errors)
        check_attribute_in_list(software, 'tags', 'name', tags_list, errors)
        check_attribute_in_list(software, 'platforms', 'name', platforms_list, errors)
        check_redirect_sections_empty(step, software, tags_with_redirect, errors)
        check_external_link_syntax(software, errors)
        check_not_archived(software, errors)
        check_last_updated(software, step, errors)
        check_boolean_attributes(software, errors)
    for license in licenses_list:
        check_required_fields(license, errors, required_fields=LICENSES_REQUIRED_FIELDS)
    for (root, dirs, files) in os.walk(step['module_options']['source_directory'] + '/software'):
        for filename in files:
            single_yaml_data = load_yaml_data(os.path.join(root, filename))
            check_filename_is_kebab_case_software_name(filename, single_yaml_data, errors)
    if errors:
        logging.error("处理过程中出现错误")
        sys.exit(1)
