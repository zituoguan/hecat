"""hecat - 通用工具函数"""
import sys
import os
import ruamel.yaml
import logging

def list_files(directory):
    """列出目录中的文件，返回按字母顺序排序的列表"""
    source_files = []
    for _, _, files in os.walk(directory):
        for file in files:
            source_files.append(file)
    return source_files

def to_kebab_case(string):
    """将字符串转换为 kebab-case，移除一些特殊字符"""
    replacements = {
        ' ': '-',
        ':': '-',
        '(': '',
        ')': '',
        '&': '',
        '/': '',
        ',': '',
        '*': '',
        '\\': '',
        '<': '',
        '>': '',
        '|': '',
        '?': '',
        '"': '',
    }
    newstring = string.translate(str.maketrans(replacements)).lower()
    return newstring

def load_yaml_data(path, sort_key=False):
    """从 YAML 源文件加载数据
    如果路径是文件，数据将直接从中加载
    如果路径是目录，数据将通过将目录中每个文件的内容添加到列表中来加载
    如果传递了 sort_key=SOMEKEY，则项目将按指定键按字母顺序排序"""
    yaml = ruamel.yaml.YAML(typ='rt')
    data = []
    if os.path.isfile(path):
        logging.debug('正在从 %s 加载数据', path)
        with open(path, 'r', encoding="utf-8") as yaml_data:
            data = yaml.load(yaml_data)
        if sort_key:
            data = sorted(data, key=lambda k: k[sort_key].upper())
        return data
    elif os.path.isdir(path):
        for file in sorted(list_files(path)):
            source_file = path + '/' + file
            logging.debug('正在从 %s 加载数据', source_file)
            with open(source_file, 'r', encoding="utf-8") as yaml_data:
                item = yaml.load(yaml_data)
                data.append(item)
            if sort_key:
                data = sorted(data, key=lambda k: k[sort_key].upper())
        return data
    else:
        logging.error('%s 不是文件或目录', path)
        sys.exit(1)

def load_config(config_file):
    """从配置文件加载步骤/设置"""
    yaml = ruamel.yaml.YAML(typ='rt')
    logging.debug('正在从 %s 加载配置', config_file)
    if not os.path.isfile(config_file):
        logging.error('配置文件 %s 不存在')
        sys.exit(1)
    with open(config_file, 'r', encoding="utf-8") as cfg:
        config = yaml.load(cfg)
    return config

def render_markdown_licenses(step, licenses, back_to_top_url=None):
    """渲染 markdown 格式的许可证列表"""
    if back_to_top_url is not None:
        markdown_licenses = '--------------------\n\n## List of Licenses\n\n**[`^        back to top        ^`](' + back_to_top_url + ')**\n\n'
    else:
        markdown_licenses = '\n--------------------\n\n## 许可证清单\n\n'
    
    for _license in licenses:
        # Check if exclude_licenses exists and contains the identifier
        if 'exclude_licenses' in step['module_options'] and step['module_options']['exclude_licenses']:
            if _license['identifier'] in step['module_options']['exclude_licenses']:
                logging.debug('许可证标识符 %s 列在 exclude_licenses 中，跳过', _license['identifier'])
                continue
        # Check if include_licenses exists and does not contain the identifier
        elif 'include_licenses' in step['module_options'] and step['module_options']['include_licenses']:
            if _license['identifier'] not in step['module_options']['include_licenses']:
                logging.debug('许可证标识符 %s 未列在 include_licenses 中，跳过', _license['identifier'])
                continue
        
        try:
            markdown_licenses += '- `{}` - [{}]({})\n'.format(
                _license['identifier'],
                _license['name'],
                _license['url'])
        except KeyError as err:
            logging.error('许可证 %s 中缺少字段: KeyError: %s', _license, err)
            sys.exit(1)
    
    return markdown_licenses

def write_data_file(step, items):
    """将更新后的数据写回数据文件"""
    yaml = ruamel.yaml.YAML(typ='rt')
    yaml.indent(sequence=2, offset=0)
    yaml.width = 99999
    with open(step['module_options']['data_file'] + '.tmp', 'w', encoding="utf-8") as temp_yaml_file:
        logging.info('写入临时数据文件 %s', step['module_options']['data_file'] + '.tmp')
        yaml.dump(items, temp_yaml_file)
    logging.info('写入数据文件 %s', step['module_options']['data_file'])
    os.rename(step['module_options']['data_file'] + '.tmp', step['module_options']['data_file'])
    