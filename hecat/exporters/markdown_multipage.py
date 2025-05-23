"""将 YAML 数据导出到一个多页 Markdown 网站，可用于使用 Sphinx 生成 HTML 网站
- 一个列出所有项目的主 index.html 页面
- 每个标签的页面
这将在 output_directory/md 中输出一个中间 Markdown 网站。必须使用 sphinx (https://www.sphinx-doc.org/) 生成最终的 HTML 网站

$ git clone https://github.com/awesome-selfhosted/awesome-selfhosted-data tests/awesome-selfhosted-data
$ $EDITOR .hecat.yml
$ hecat

# .hecat.yml
steps:
  - name: 将 YAML 数据导出到多页 Markdown/HTML 网站
    module: exporters/markdown_multipage
    module_options:
      source_directory: tests/awesome-selfhosted-data # 包含 YAML 数据的目录
      output_directory: tests/awesome-selfhosted-html # 写入 Markdown 页面的目录
      exclude_licenses: # 可选，默认 []
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

$ sphinx-build -b html -c CONFIG_DIR/ SOURCE_DIR/ OUTPUT_DIR/
CONFIG_DIR/ 是包含 conf.py sphinx 配置文件 的目录，示例见 https://github.com/nodiscc/hecat/blob/master/tests/conf.py
SOURCE_DIR/ 是包含由 hecat/markdown_multipage.py 生成的 Markdown 网站的目录
OUTPUT_DIR/ 是 HTML 网站的输出目录
当前，Sphinx 配置文件 (CONFIG_DIR/conf.py) 中预期有以下设置
  html_theme = 'furo'
  extensions = ['myst_parser', 'sphinx_design']
  myst_enable_extensions = ['fieldlist']
  html_static_path = ['SOURCE_DIR/_static']
  html_css_files = ['custom.css']


输出目录结构（运行 sphinx-build 后）：
├── html # 发布此目录的内容
│   ├── genindex.html
│   ├── index.html
│   ├── search.html
│   ├── searchindex.js
│   ├── _sphinx_design_static
│   │   ├── *.css
│   │   └── *.js
│   ├── _static
│   │   ├── *.png
│   │   ├── *.svg
│   │   ├── custom.css
│   │   ├── *.css
│   │   ├── *.js
│   │   ├── favicon.ico
│   │   └── opensearch.xml
│   └── tags
│       ├── analytics.html
│       ├── archiving-and-digital-preservation-dp.html
│       ├── ....html
│       └── wikis.html
└── md # 中间 Markdown 版本，可以丢弃
    ├── index.md
    └── tags

源 YAML 目录结构和软件/平台数据的格式在 markdown_singlepage.py 中有文档说明。
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import urllib
import ruamel.yaml
from jinja2 import Template
from ..utils import load_yaml_data, to_kebab_case, render_markdown_licenses

yaml = ruamel.yaml.YAML(typ='safe')
yaml.indent(sequence=4, offset=2)

MARKDOWN_CSS="""
    .tag {
        background-color: #DBEAFE;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #1E40AF;
        font-weight: bold;
        display: inline-block;
    }
    .tag a {
        text-decoration: none
    }
    .platform {
        background-color: #B0E6A3;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #2B4026;
        font-weight: bold;
        display: inline-block;
    }
    .platform a {
        text-decoration: none;
        color: #2B4026;
    }
    .license-box {
        background-color: #A7C7F9;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        display: inline-block;
    }
    .license-link {
        color: #173B80;
        font-weight: bold;
        text-decoration: none
    }
    .stars {
        background-color: #FFFCAB;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #856000;
        font-weight: bold;
        display: inline-block;
    }
    .updated-at {
        background-color: #EFEFEF;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #444444;
        display: inline-block;
        font-weight: bold
    }
    .orangebox {
        background-color: #FD9D49;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #FFFFFF;
        display: inline-block;
        font-weight: bold
    }
    .redbox {
        background-color: #FD4949;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        color: #FFFFFF;
        display: inline-block;
        font-weight: bold
    }
    .external-link-box {
        background-color: #1E40AF;
        border-radius: 5px;
        padding: 2px 8px 0px 8px;
        display: inline-block;
    }
    .external-link {
        color: #DBEAFE;
        font-weight: bold;
        text-decoration: none
    }
    .external-link a:hover {
        color: #FFF;
    }
    .sd-octicon {
        vertical-align: inherit
    }
    hr.docutils {
        margin: 1rem 0;
    }
    .sidebar-brand-text {
        font-size: 1.4rem;
        margin: 0 auto;
    }
"""

MARKDOWN_INDEX_CONTENT_HEADER="""
--------------------

## 软件

此页面列出了所有项目。使用侧边栏中的链接或点击 {octicon}`tag;0.8em;octicon` 标签按类别浏览项目。
"""

# 软件列表项模板 - 带链接到软件详情页面
SOFTWARE_JINJA_MARKDOWN="""
--------------------

### <a href="{{software_url }}">{{ software['name'] }}</a>

{{ software['description'] }}

<span class="external-link-box"><a class="external-link" href="{{ software['website_url'] }}">{% raw %}{octicon}{% endraw %}`globe;0.8em;octicon` 网站</a></span>
<span class="external-link-box"><a class="external-link" href="{% if software['source_code_url'] is defined %}{{ software['source_code_url'] }}{% else %}{{ software['website_url'] }}{% endif %}">{% raw %}{octicon}{% endraw %}`git-branch;0.8em;octicon` 源代码</a></span>
{% if software['related_software_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ software['related_software_url'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` 相关软件</a></span>
{% endif -%}
{% if software['demo_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ software['demo_url'] }}">{% raw %}{octicon}{% endraw %}`play;0.8em;octicon` 演示</a></span>
{% endif %}

<span class="stars">★{% if software['stargazers_count'] is defined %}{{ software['stargazers_count'] }}{% else %}?{% endif %}</span>
<span class="{{ date_css_class }}" title="最后更新日期">{% raw %}{octicon}{% endraw %}`clock;0.8em;octicon` {% if software['updated_at'] is defined %}{{ software['updated_at'] }}{% else %}?{% endif %}</span>
{% for platform in platforms %}<span class="platform"><a href="{{ platform['href'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` {{ platform['name'] }}</a> </span> {% endfor %}
{% for license in software['licenses'] %}<span class="license-box"><a class="license-link" href="{{ licenses_relative_url }}">{% raw %}{octicon}{% endraw %}`law;0.8em;octicon` {{ license }}</a> </span> {% endfor %}
{% if software['depends_3rdparty'] is defined and software['depends_3rdparty'] %}<span class="orangebox" title="依赖于用户无法控制的专有服务">⚠ 反特性</span>{% endif %}

{% for tag in tags %}<span class="tag"><a href="{{ tag['href'] }}">{% raw %}{octicon}{% endraw %}`tag;0.8em;octicon` {{ tag['name'] }}</a> </span>
{% endfor %}

"""

TAG_HEADER_JINJA_MARKDOWN="""

# {{ item['name'] }}

{{ item['description']}}

{% if item['related_tags'] is defined %}```{admonition} 相关标签
{% for related_tag in item['related_tags'] %}- [{{ related_tag }}]({{ to_kebab_case(related_tag) }}.md)
{% endfor %}
```
{% endif %}
{% if item['external_links'] is defined %}```{seealso}
{% for link in item['external_links'] %}- [{{ link['title'] }}]({{ link['url'] }})
{% endfor %}
{% endif %}
{% if item['redirect'] is defined %}```{important}
**请改为访问 {% for redirect in item['redirect'] %}[{{ redirect['title'] }}]({{ redirect['url'] }}){% if not loop.last %}{{', '}}{% endif %}{% endfor %}**
```{% endif %}

"""

MARKDOWN_TAGPAGE_CONTENT_HEADER="""
--------------------

## 软件

此页面列出了该类别中的所有项目。使用 [所有项目的索引](../index.md)、侧边栏，或点击 {octicon}`tag;0.8em;octicon` 标签浏览其他类别。

"""


PLATFORM_HEADER_JINJA_MARKDOWN="""

# {{ item['name'] }}

{{ item['description']}}

"""

MARKDOWN_PLATFORMPAGE_CONTENT_HEADER="""
--------------------

## 软件

此页面列出了使用此编程语言或部署平台的所有项目。仅考虑主要的服务器端需求、打包或分发格式。

"""

# 软件页面头部模板
SOFTWARE_HEADER_JINJA_MARKDOWN="""

# {{ item['name'] }}

{{ item['description'] }}

"""

# 软件页面内容头部
MARKDOWN_SOFTWAREPAGE_CONTENT_HEADER="""
--------------------

## 详细信息

"""

# 软件详情内容模板
SOFTWARE_DETAIL_JINJA_MARKDOWN="""

<span class="external-link-box"><a class="external-link" href="{{ software['website_url'] }}">{% raw %}{octicon}{% endraw %}`globe;0.8em;octicon` 网站</a></span>
<span class="external-link-box"><a class="external-link" href="{% if software['source_code_url'] is defined %}{{ software['source_code_url'] }}{% else %}{{ software['website_url'] }}{% endif %}">{% raw %}{octicon}{% endraw %}`git-branch;0.8em;octicon` 源代码</a></span>
{% if software['related_software_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ software['related_software_url'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` 相关软件</a></span>
{% endif -%}
{% if software['demo_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ software['demo_url'] }}">{% raw %}{octicon}{% endraw %}`play;0.8em;octicon` 演示</a></span>
{% endif %}

<span class="stars">★{% if software['stargazers_count'] is defined %}{{ software['stargazers_count'] }}{% else %}?{% endif %}</span>
<span class="{{ date_css_class }}" title="最后更新日期">{% raw %}{octicon}{% endraw %}`clock;0.8em;octicon` {% if software['updated_at'] is defined %}{{ software['updated_at'] }}{% else %}?{% endif %}</span>
{% for platform in platforms %}<span class="platform"><a href="{{ platform['href'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` {{ platform['name'] }}</a> </span> {% endfor %}
{% for license in software['licenses'] %}<span class="license-box"><a class="license-link" href="{{ licenses_relative_url }}">{% raw %}{octicon}{% endraw %}`law;0.8em;octicon` {{ license }}</a> </span> {% endfor %}
{% if software['depends_3rdparty'] is defined and software['depends_3rdparty'] %}<span class="orangebox" title="依赖于用户无法控制的专有服务">⚠ 反特性</span>{% endif %}

{% for tag in tags %}<span class="tag"><a href="{{ tag['href'] }}">{% raw %}{octicon}{% endraw %}`tag;0.8em;octicon` {{ tag['name'] }}</a> </span>
{% endfor %}

{% if software['features'] is defined and software['features'] %}
### 功能

{% for feature in software['features'] %}- {{ feature }}
{% endfor %}
{% endif %}

{% if software['screenshots'] is defined and software['screenshots'] %}
### 截图

{% for screenshot in software['screenshots'] %}- [{{ screenshot['title'] }}]({{ screenshot['url'] }})
{% endfor %}
{% endif %}

{% if software['documentation'] is defined and software['documentation'] %}
### 文档

- [{{ software['documentation']['title'] if 'title' in software['documentation'] else '文档' }}]({{ software['documentation']['url'] if 'url' in software['documentation'] else software['documentation'] }})
{% endif %}
"""

# 相关软件模板
SOFTWARE_RELATED_JINJA_MARKDOWN="""
## 相关软件

以下软件与 {{ software['name'] }} 有相似的标签：

--------------------

{% for related in related_software_list %}
### <a href="{{ software_relative_url + to_kebab_case(related['name']) + '.html' }}">{{ related['name'] }}</a>

{% if related['description'] is defined %}{{ related['short_description'] }}{% endif %}

<span class="external-link-box"><a class="external-link" href="{{ related['website_url'] }}">{% raw %}{octicon}{% endraw %}`globe;0.8em;octicon` 网站</a></span>
<span class="external-link-box"><a class="external-link" href="{% if related['source_code_url'] is defined %}{{ related['source_code_url'] }}{% else %}{{ related['website_url'] }}{% endif %}">{% raw %}{octicon}{% endraw %}`git-branch;0.8em;octicon` 源代码</a></span>
{% if related['related_software_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ related['related_software_url'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` 相关软件</a></span>
{% endif -%}
{% if related['demo_url'] is defined -%}<span class="external-link-box"><a class="external-link" href="{{ related['demo_url'] }}">{% raw %}{octicon}{% endraw %}`play;0.8em;octicon` 演示</a></span>
{% endif %}

<span class="stars">★{% if related['stargazers_count'] is defined %}{{ related['stargazers_count'] }}{% else %}?{% endif %}</span>
<span class="{{ date_css_class }}" title="最后更新日期">{% raw %}{octicon}{% endraw %}`clock;0.8em;octicon` {% if related['updated_at'] is defined %}{{ related['updated_at'] }}{% else %}?{% endif %}</span>
{% for platform in related['display_platforms'] %}<span class="platform"><a href="{{ platform['href'] }}">{% raw %}{octicon}{% endraw %}`package;0.8em;octicon` {{ platform['name'] }}</a> </span> {% endfor %}
{% for license in related['licenses'] %}<span class="license-box"><a class="license-link" href="{{ licenses_relative_url }}">{% raw %}{octicon}{% endraw %}`law;0.8em;octicon` {{ license }}</a> </span> {% endfor %}
{% if related['depends_3rdparty'] is defined and related['depends_3rdparty'] %}<span class="orangebox" title="依赖于用户无法控制的专有服务">⚠ 反特性</span>{% endif %}

{% for tag in related['display_tags'] %}<span class="tag"><a href="{{ tag['href'] }}">{% raw %}{octicon}{% endraw %}`tag;0.8em;octicon` {{ tag['name'] }}</a> </span>
{% endfor %}
{% endfor %}

"""

def render_markdown_software_detail(software, tags_relative_url='./', platforms_relative_url='./', licenses_relative_url='#id4'):
    """渲染软件详细信息页面的内容"""
    tags_dicts_list = []
    platforms_dicts_list = []
    
    for tag in software['tags']:
        tags_dicts_list.append({
            "name": tag, 
            "href": tags_relative_url + urllib.parse.quote(to_kebab_case(tag)) + '.html'
        })
    
    for platform in software['platforms']:
        platforms_dicts_list.append({
            "name": platform, 
            "href": platforms_relative_url + urllib.parse.quote(to_kebab_case(platform)) + '.html'
        })
    
    date_css_class = 'updated-at'
    if 'updated_at' in software:
        last_update_time = datetime.strptime(software['updated_at'], "%Y-%m-%d")
        if last_update_time < datetime.now() - timedelta(days=365):
            date_css_class = 'redbox'
        elif last_update_time < datetime.now() - timedelta(days=186):
            date_css_class = 'orangebox'
            
    detail_template = Template(SOFTWARE_DETAIL_JINJA_MARKDOWN)
    markdown_detail = detail_template.render(
        software=software,
        tags=tags_dicts_list,
        platforms=platforms_dicts_list,
        date_css_class=date_css_class,
        licenses_relative_url=licenses_relative_url
    )
    
    return markdown_detail

def render_related_software(software, software_list, tags_relative_url='./', platforms_relative_url='./', software_relative_url='./', licenses_relative_url='#id4'):
    """使用模板渲染与当前软件相关的软件列表"""
    related_software_list = []
    software_tags = set(software['tags'])
    
    # 找出共享至少一个标签的软件
    for other_software in software_list:
        if other_software['name'] != software['name']:  # 排除自身
            other_tags = set(other_software['tags'])
            if software_tags.intersection(other_tags):  # 如果有共同标签
                # 准备相关软件的数据
                related_software = other_software.copy()
                
                # 准备标签数据（最多显示3个）
                display_tags = []
                display_platforms = []
                for tag in related_software['tags']:
                    display_tags.append({
                        'name': tag,
                        'href': tags_relative_url + urllib.parse.quote(to_kebab_case(tag)) + '.html'
                    })
                related_software['display_tags'] = display_tags
                for platform in related_software['platforms']:
                    display_platforms.append({
                        'name': platform,
                        'href': platforms_relative_url + urllib.parse.quote(to_kebab_case(platform)) + '.html'
                    })
                related_software['display_platforms'] = display_platforms
                related_software_list.append(related_software)

    # 只保留前5个相关软件
    #related_software_list = related_software_list[:5]

    # 相关软件的标签和平台

    # 如果没有相关软件，返回空字符串
    if not related_software_list:
        return ""
    
    # 使用模板渲染相关软件列表
    related_template = Template(SOFTWARE_RELATED_JINJA_MARKDOWN)
    related_template.globals['to_kebab_case'] = to_kebab_case  # 添加全局函数以在模板中使用
    
    markdown_related = related_template.render(
        software=software,
        related_software_list=related_software_list,
        software_relative_url=software_relative_url,
        tags_relative_url=tags_relative_url,
        platforms_relative_url=platforms_relative_url,
        licenses_relative_url=licenses_relative_url
    )
    
    return markdown_related

def render_markdown_software(software, tags_relative_url='tags/', platforms_relative_url='platforms/', software_relative_url='software/', licenses_relative_url='#id4'):
    """将软件项目信息渲染为 Markdown 列表项"""
    tags_dicts_list = []
    platforms_dicts_list = []
    
    for tag in software['tags']:
        tags_dicts_list.append({
            "name": tag, 
            "href": tags_relative_url + urllib.parse.quote(to_kebab_case(tag)) + '.html'
        })
    
    for platform in software['platforms']:
        platforms_dicts_list.append({
            "name": platform, 
            "href": platforms_relative_url + urllib.parse.quote(to_kebab_case(platform)) + '.html'
        })
    
    date_css_class = 'updated-at'
    if 'updated_at' in software:
        last_update_time = datetime.strptime(software['updated_at'], "%Y-%m-%d")
        if last_update_time < datetime.now() - timedelta(days=365):
            date_css_class = 'redbox'
        elif last_update_time < datetime.now() - timedelta(days=186):
            date_css_class = 'orangebox'
    
    # 创建软件页面链接
    software_url = software_relative_url + urllib.parse.quote(to_kebab_case(software['name'])) + '.html'
    
    software_template = Template(SOFTWARE_JINJA_MARKDOWN)
    markdown_software = software_template.render(
        software=software,
        software_url=software_url,
        tags=tags_dicts_list,
        platforms=platforms_dicts_list,
        date_css_class=date_css_class,
        licenses_relative_url=licenses_relative_url
    )
    
    return markdown_software

def render_item_page(step, item_type, item, software_list):
    """
    为标签、平台或软件渲染页面。
    :param dict step: 步骤配置
    :param str item_type: 要渲染的页面类型（标签、平台或软件）
    :param dict item: 要渲染的项（标签、平台或软件对象）
    :param list software_list: 完整的软件列表（字典列表）
    """
    logging.debug('正在渲染 %s %s 的页面', item_type, item['name'])
    
    if item_type == 'tag':
        markdown_fieldlist = ''
        header_template = Template(TAG_HEADER_JINJA_MARKDOWN)
        content_header = MARKDOWN_TAGPAGE_CONTENT_HEADER
        match_key = 'tags'
        tags_relative_url = './'
        platforms_relative_url = '../platforms/'
        software_relative_url = '../software/'
        output_dir = step['module_options']['output_directory'] + '/md/tags/'
    elif item_type == 'platform':
        markdown_fieldlist = ':orphan:\n'
        header_template = Template(PLATFORM_HEADER_JINJA_MARKDOWN)
        content_header = MARKDOWN_PLATFORMPAGE_CONTENT_HEADER
        match_key = 'platforms'
        tags_relative_url = '../tags/'
        platforms_relative_url = './'
        software_relative_url = '../software/'
        output_dir = step['module_options']['output_directory'] + '/md/platforms/'
    elif item_type == 'software':
        markdown_fieldlist = ':orphan:\n'
        header_template = Template(SOFTWARE_HEADER_JINJA_MARKDOWN)
        content_header = MARKDOWN_SOFTWAREPAGE_CONTENT_HEADER
        match_key = None  # 软件页面不需要匹配键
        tags_relative_url = '../tags/'
        platforms_relative_url = '../platforms/'
        software_relative_url = './'
        output_dir = step['module_options']['output_directory'] + '/md/software/'
        # 确保输出目录存在
        try:
            os.mkdir(output_dir)
        except FileExistsError:
            pass
    else:
        logging.error('item_type 的值无效，必须是 tag、platform 或 software')
        sys.exit(1)
    
    header_template.globals['to_kebab_case'] = to_kebab_case
    markdown_page_header = header_template.render(item=item)
    
    if item_type == 'software':
        # 渲染软件详情页面
        markdown_software_detail = ''
        if any(license in item['licenses'] for license in step['module_options']['exclude_licenses']):
            logging.debug("%s 的许可证在 exclude_licenses 中", item['name'])
        else:
            markdown_software_detail = render_markdown_software_detail(
                item,
                tags_relative_url=tags_relative_url,
                platforms_relative_url=platforms_relative_url,
                licenses_relative_url='../index.html#id4'
            )
        
        # 渲染相关软件
        markdown_related_software = ''
        if any(license in item['licenses'] for license in step['module_options']['exclude_licenses']):
            logging.debug("%s 的许可证在 exclude_licenses 中", item['name'])
        else:
            markdown_related_software = render_related_software(
                item,
                software_list,
                tags_relative_url=tags_relative_url,
                platforms_relative_url=platforms_relative_url,
                software_relative_url=software_relative_url,
                licenses_relative_url='../index.html#id4'
            )
        
        # 组合完整页面
        markdown_page = '{}{}{}{}{}'.format(
            markdown_fieldlist,
            markdown_page_header,
            content_header,
            markdown_software_detail,
            markdown_related_software
        )
    else:
        # 原有的标签和平台页面渲染逻辑
        markdown_software_list = ''
        for software in software_list:
            if any(license in software['licenses'] for license in step['module_options']['exclude_licenses']):
                logging.debug("%s 的许可证在 exclude_licenses 中，跳过", software['name'])
            elif any(value == item['name'] for value in software[match_key]):
                markdown_software_list = markdown_software_list + render_markdown_software(
                    software,
                    tags_relative_url=tags_relative_url,
                    platforms_relative_url=platforms_relative_url,
                    software_relative_url=software_relative_url,
                    licenses_relative_url='../index.html#id4'
                )
        
        if markdown_software_list:
            markdown_page = '{}{}{}{}'.format(
                markdown_fieldlist,
                markdown_page_header,
                content_header,
                markdown_software_list
            )
        else:
            markdown_page = markdown_page_header
    
    # 确定输出文件名
    output_file_name = output_dir + to_kebab_case(item['name']) + '.md'
    
    with open(output_file_name, 'w+', encoding="utf-8") as outfile:
        logging.debug('正在写入输出文件 %s', output_file_name)
        outfile.write(markdown_page)

def render_markdown_toctree(tags):
    """渲染 toctree 块"""
    logging.debug('正在渲染 toctree')
    tags_files_list = ''
    for tag in tags:
        tag_file_name = 'tags/' + to_kebab_case(tag['name'] + '.md')
        tags_files_list = '{}\n{}'.format(tags_files_list, tag_file_name)
    markdown_toctree = '\n```{{toctree}}\n:maxdepth: 1\n:hidden:\n{}\n```\n\n'.format(tags_files_list)
    return markdown_toctree

def render_markdown_multipage(step):
    """
    按字母顺序渲染所有软件的单页 Markdown 列表
    添加头部/尾部
    还为每个软件项目创建单独的页面
    """
    if 'exclude_licenses' not in step['module_options']:
        step['module_options']['exclude_licenses'] = []
    if 'output_file' not in step['module_options']:
        step['module_options']['output_file'] = 'index.md'
    
    tags = load_yaml_data(step['module_options']['source_directory'] + '/tags', sort_key='name')
    platforms = load_yaml_data(step['module_options']['source_directory'] + '/platforms', sort_key='name')
    software_list = load_yaml_data(step['module_options']['source_directory'] + '/software')
    licenses = load_yaml_data(step['module_options']['source_directory'] + '/licenses.yml')
    
    # 使用 fieldlist myst-parser 扩展将 TOC 深度限制为 2
    markdown_fieldlist = ':tocdepth: 2\n'
    markdown_content_header = MARKDOWN_INDEX_CONTENT_HEADER
    
    with open(step['module_options']['source_directory'] + '/markdown/header.md', 'r', encoding="utf-8") as header_file:
        markdown_header = header_file.read()
    
    with open(step['module_options']['source_directory'] + '/markdown/footer.md', 'r', encoding="utf-8") as footer_file:
        markdown_footer = footer_file.read()
    
    markdown_toctree = render_markdown_toctree(tags)
    markdown_software_list = ''
    
    for software in software_list:
        if any(license in software['licenses'] for license in step['module_options']['exclude_licenses']):
            logging.debug("%s 的许可证在 exclude_licenses 中，跳过", software['name'])
        else:
            markdown_software_list = markdown_software_list + render_markdown_software(
                software,
                software_relative_url='software/'
            )
    
    markdown_licenses = render_markdown_licenses(step, licenses)
    
    markdown = '{}{}{}{}{}{}{}'.format(
        markdown_fieldlist,
        markdown_header,
        markdown_content_header,
        markdown_toctree,
        markdown_software_list,
        markdown_licenses,
        markdown_footer
    )
    
    output_file_name = step['module_options']['output_directory'] + '/md/' + step['module_options']['output_file']
    
    # 创建必要的目录
    for directory in ['/md/', '/md/tags/', '/md/platforms/', '/md/software/']:
        try:
            os.mkdir(step['module_options']['output_directory'] + directory)
        except FileExistsError:
            pass
    
    with open(output_file_name, 'w+', encoding="utf-8") as outfile:
        logging.info('正在写入输出文件 %s', output_file_name)
        outfile.write(markdown)
    
    logging.info('正在渲染标签页面')
    for tag in tags:
        render_item_page(step, 'tag', tag, software_list)
    
    logging.info('正在渲染平台页面')
    for platform in platforms:
        render_item_page(step, 'platform', platform, software_list)
    
    logging.info('正在渲染软件页面')
    for software in software_list:
        if not any(license in software['licenses'] for license in step['module_options']['exclude_licenses']):
            render_item_page(step, 'software', software, software_list)
    
    try:
        os.mkdir(step['module_options']['output_directory'] + '/_static')
    except FileExistsError:
        pass
    
    output_css_file_name = step['module_options']['source_directory'] + '/_static/custom.css'
    with open(output_css_file_name, 'w+', encoding="utf-8") as outfile:
        logging.info('正在写入输出 CSS 文件 %s', output_css_file_name)
        outfile.write(MARKDOWN_CSS)
        