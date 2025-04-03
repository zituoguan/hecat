# 新增软件页面的头部模板
SOFTWARE_HEADER_JINJA_MARKDOWN="""

# {{ item['name'] }}

{{ item['description'] }}

"""

# 新增软件页面的内容头部
MARKDOWN_SOFTWAREPAGE_CONTENT_HEADER="""
--------------------

## 详细信息

"""

# 新增软件详情内容的 Jinja 模板
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

### 标签

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

# 软件相关项目部分
SOFTWARE_RELATED_JINJA_MARKDOWN="""
## 相关软件

以下软件与 {{ software['name'] }} 有相似的标签：

"""

def render_markdown_software_detail(software, tags_relative_url='./', platforms_relative_url='./', licenses_relative_url='#list-of-licenses'):
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

def render_related_software(software, software_list, tags_relative_url='./', platforms_relative_url='./', software_relative_url='./', licenses_relative_url='#list-of-licenses'):
    """渲染与当前软件相关的软件列表"""
    related_software_list = []
    software_tags = set(software['tags'])
    
    # 找出共享至少一个标签的软件
    for other_software in software_list:
        if other_software['name'] != software['name']:  # 排除自身
            other_tags = set(other_software['tags'])
            if software_tags.intersection(other_tags):  # 如果有共同标签
                related_software_list.append(other_software)
    
    # 只保留前5个相关软件
    related_software_list = related_software_list[:5]
    
    # 如果没有相关软件，返回空字符串
    if not related_software_list:
        return ""
    
    # 添加相关软件标题
    related_template = Template(SOFTWARE_RELATED_JINJA_MARKDOWN)
    markdown_related = related_template.render(software=software)
    
    # 为每个相关软件添加简短描述
    for related in related_software_list:
        software_url = software_relative_url + to_kebab_case(related['name']) + '.html'
        markdown_related += f"### [{related['name']}]({software_url})\n\n"
        
        # 添加简短描述
        if 'description' in related:
            # 只取描述的第一句或前100个字符
            desc = related['description'].split('.')[0] + '.' if '.' in related['description'] else related['description']
            if len(desc) > 100:
                desc = desc[:97] + '...'
            markdown_related += f"{desc}\n\n"
        
        # 添加标签
        tags_list = []
        for tag in related['tags'][:3]:  # 最多显示3个标签
            tag_url = tags_relative_url + urllib.parse.quote(to_kebab_case(tag)) + '.html'
            tags_list.append(f"[{tag}]({tag_url})")
        
        if tags_list:
            markdown_related += f"标签: {', '.join(tags_list)}\n\n"
    
    return markdown_related

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
        markdown_software_detail = render_markdown_software_detail(
            item,
            tags_relative_url=tags_relative_url,
            platforms_relative_url=platforms_relative_url,
            licenses_relative_url='../index.html#list-of-licenses'
        )
        
        # 渲染相关软件
        markdown_related_software = render_related_software(
            item,
            software_list,
            tags_relative_url=tags_relative_url,
            platforms_relative_url=platforms_relative_url,
            software_relative_url=software_relative_url,
            licenses_relative_url='../index.html#list-of-licenses'
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
                # 添加指向软件详情页面的链接
                markdown_software_list = markdown_software_list + render_markdown_software(
                    software,
                    tags_relative_url=tags_relative_url,
                    platforms_relative_url=platforms_relative_url,
                    software_relative_url=software_relative_url,  # 新增软件页面的相对URL
                    licenses_relative_url='../index.html#list-of-licenses'
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

# 修改现有的render_markdown_software函数以包含到软件详情页面的链接
def render_markdown_software(software, tags_relative_url='tags/', platforms_relative_url='platforms/', software_relative_url='software/', licenses_relative_url='#list-of-licenses'):
    """将软件项目信息渲染为 Markdown 列表项"""
    tags_dicts_list = []
    platforms_dicts_list = []
    
    for tag in software['tags']:
        tags_dicts_list.append({"name": tag, "href": tags_relative_url + urllib.parse.quote(to_kebab_case(tag)) + '.html'})
    
    for platform in software['platforms']:
        platforms_dicts_list.append({"name": platform, "href": platforms_relative_url + urllib.parse.quote(to_kebab_case(platform)) + '.html'})
    
    date_css_class = 'updated-at'
    if 'updated_at' in software:
        last_update_time = datetime.strptime(software['updated_at'], "%Y-%m-%d")
        if last_update_time < datetime.now() - timedelta(days=365):
            date_css_class = 'redbox'
        elif last_update_time < datetime.now() - timedelta(days=186):
            date_css_class = 'orangebox'
    
    # 创建软件页面链接
    software_page_url = software_relative_url + to_kebab_case(software['name']) + '.html'
    
    # 修改软件名称部分，使其成为链接
    SOFTWARE_JINJA_MARKDOWN_WITH_LINK = SOFTWARE_JINJA_MARKDOWN.replace(
        "### {{ software['name'] }}", 
        "### [{{ software['name'] }}](" + software_page_url + ")"
    )
    
    software_template = Template(SOFTWARE_JINJA_MARKDOWN_WITH_LINK)
    markdown_software = software_template.render(
        software=software,
        tags=tags_dicts_list,
        platforms=platforms_dicts_list,
        date_css_class=date_css_class,
        licenses_relative_url=licenses_relative_url
    )
    
    return markdown_software

# 修改render_markdown_multipage函数以添加软件页面渲染
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
            # 使用修改后的函数，它将在软件名上添加链接
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
        