"""将数据渲染为HTML表格
# $ cat hecat.yml
steps:
  - name: 将shaarli数据导出为HTML表格
    module: importers/shaarli_api
    module_options:
      source_file: shaarli.yml # 将从中加载数据的文件
      output_file: index.html # (默认 index.html) 输出HTML表格文件
      html_title: "hecat HTML导出" # (默认 "hecat HTML export") 输出HTML标题
      favicon_base64: "iVBORw0KGgoAAAAN..." # (默认为默认favicon) base64编码的png favicon
      description_format: paragraph # (details/paragraph, 默认 details) 将描述包装在HTML details标签中
      archive_dir: webpages # (默认 webpages) 网页归档基础目录的路径(archive_webpages模块的output_directory)

源目录结构:
└── shaarli.yml

输出目录结构:
└── index.html
"""

import sys
import logging
from datetime import datetime
from jinja2 import Template
import markdown
from ..utils import load_yaml_data

HTML_JINJA = """
<html>
<head>
<title>{{ html_title }}</title>
<link rel="icon" href="data:image/png;base64,{{ favicon_base64 }}">
<style>
  body {
    margin: 10px 20px;
    padding: 0;
    font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;
    background-color: #F8F8F8;
  }

  table {
    width: 100%;
    min-width: 960px;
    border-collapse: collapse;
  }

  a {
    text-decoration: none;
  }

  table, th, td {
    padding: 1px;
    text-align: left;
    border-bottom: 1px solid #ddd;
    font-size: 90%;
  }

  tr:hover {
    background-color: #E6F3F9;
  }

  thead {
    font-weight: bold;
    background-color: #EAEAEA;
  }

  code {
    background-color: #EAEAEA;
    padding: 1px;
    font-family: Monospace;
    font-size: 110%;
    border-radius: 3px;
    color: #222;
  }

  ul, p {
    margin-top: auto;
  }

  ul {
    padding-left: 20px;
  }

  .searchbar {
    background-color: #EAEAEA;
    padding: 10px;
  }

  .date-column {
    min-width: 130px;
  }

  .title-column {
    min-with: 480px;
    max-width: 900px;
  }

  blockquote {
    border-left: 2px solid #CCC;
    margin-left: 5px;
    padding-left: 5px;
    color: #666;
  }
</style>

<script>
function myFunctionTitle() {
  // 声明变量
  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById("myTitleInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");

  // 遍历所有表格行，隐藏那些不匹配搜索查询的行
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[1];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

function myFunctionTag() {
  // 声明变量
  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById("myTagInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");

  // 遍历所有表格行，隐藏那些不匹配搜索查询的行
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[3];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}
</script>


</head>
<body>
<div class="searchbar">
<input type="text" id="myTitleInput" onkeyup="myFunctionTitle()" placeholder="搜索标题/描述...">
<input type="text" id="myTagInput" onkeyup="myFunctionTag()" placeholder="搜索@标签..">
<span>{{ link_count }} 个链接</span>
<span style="font-size: 75%; color: #666; text-align: 'right';">使用 <a href="https://github.com/nodiscc/hecat">hecat</a> 构建</span>
</div>
<table id="myTable">
  <thead>
    <tr>
      <td></td>
      <td class="title-column">标题</td>
      <td class="date-column">日期</td>
      <td>标签</td>
    </tr>
  </thead>
{% for item in items %}
<tr>
<td>{% if item['archive_path'] is defined %}<a href="{{ archive_dir }}/{{ 'private' if item['private'] else 'public' }}/{{ item['archive_path'] }}">▣</a>{% elif item['archive_error'] is defined and item['archive_error'] %}⚠{% endif %}</td>
  <td class="title-column"><a href='{{ item['url'] }}'>{{ item['title'] }}</a>
  {% if item['description'] is defined and item['description'] %}<br/>{% if description_format == 'details' %}<details><summary></summary>{% elif description_format == 'paragraph' %}<p>{% endif %}{{ jinja_markdown(item['description']) }}{% if description_format == 'details' %}</details>{% elif description_format == 'paragraph' %}</p>{% endif %}{% endif %}
  </td>
  <td>{{ simple_datetime(item.created) }}</td>
  <td><code>@{{ '</code> <code>@'.join(item['tags']) }}</code></td>
<tr/>
{% endfor %}
</div>
</table>
</body>
</html>
"""

def jinja_markdown(text):
    """用于从jinja2模板内部使用markdown库的包装器"""
    return markdown.markdown(text, extensions=['fenced_code', 'pymdownx.magiclink'])

def simple_datetime(date):
    """将日期格式化为YYYY-mm-dd HH:MM:SS"""
    return datetime.strftime(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z"), "%Y-%m-%d %H:%M:%S")

def render_html_table(step):
    """将列表数据渲染为HTML表格"""
    if 'output_file' not in step['module_options']:
        step['module_options']['output_file'] = 'index.html'
    if 'html_title' not in step['module_options']:
        step['module_options']['html_title'] = 'hecat HTML导出'
    if 'favicon_base64' not in step['module_options']:
        step['module_options']['favicon_base64'] = 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAB3RJTUUH5wIEFgEeyYiWTQAAAAlQTFRFAAAALi4u////gGfi/AAAAAF0Uk5TAEDm2GYAAAABYktHRAJmC3xkAAAAKUlEQVQI12NggAPR0NAQBqlVq5YwSIaGpjBILsVFhK1MgSgBKwZrgwMAswcRaNWVOXAAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjMtMDItMDRUMjI6MDE6MzArMDA6MDB1Hpz/AAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIzLTAyLTA0VDIyOjAxOjMwKzAwOjAwBEMkQwAAAABJRU5ErkJggg=='
    if 'description_format' not in step['module_options']:
        step['module_options']['description_format'] = 'details'
    if step['module_options']['description_format'] not in ['details', 'paragraph']:
        logging.error('description_format选项的值%s无法识别。允许的值：details, paragraph', step['module_options']['description_format'])
        sys.exit(1)
    if 'archive_dir' not in step['module_options']:
        step['module_options']['archive_dir'] = 'webpages'
    data = load_yaml_data(step['module_options']['source_file'])
    link_count = len(data)
    html_template = Template(HTML_JINJA)
    html_template.globals['jinja_markdown'] = jinja_markdown
    html_template.globals['simple_datetime'] = simple_datetime
    with open(step['module_options']['output_file'], 'w+', encoding="utf-8") as html_file:
        logging.info('写入文件 %s', step['module_options']['output_file'])
        html_file.write(html_template.render(items=data,
                                            link_count=link_count,
                                            html_title=step['module_options']['html_title'],
                                            favicon_base64=step['module_options']['favicon_base64'],
                                            description_format=step['module_options']['description_format'],
                                            archive_dir=step['module_options']['archive_dir']
                                            ))
