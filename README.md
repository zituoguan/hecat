# hecat

一个围绕以纯文本 YAML 文件存储数据的通用自动化工具。

[![CI](https://github.com/nodiscc/hecat/actions/workflows/ci.yml/badge.svg)](https://github.com/nodiscc/hecat/actions)

该程序使用 YAML 文件存储各种类型项目（书签、软件项目等）的数据，并应用各种处理任务。
功能在不同模块中实现。

### 导入器

从各种输入格式导入数据：

- [importers/markdown_awesome](hecat/importers/markdown_awesome.py)：从 [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) markdown 格式导入数据
- [importers/shaarli_api](hecat/importers//shaarli_api.py)：使用 [API](https://shaarli.github.io/api-documentation/) 从 [Shaarli](https://github.com/shaarli/Shaarli) 实例导入数据

[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/tMAxhLw.png)](hecat/importers/markdown_awesome.py)


### 处理器

对 YAML 数据执行处理任务：

- [processors/github_metadata](hecat/processors/github_metadata.py)：从 GitHub API 丰富软件项目元数据（星标数、最后提交日期等）
- [processors/awesome_lint](hecat/processors/awesome_lint.py)：根据 [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) 一致性/完整性指南检查数据
- [processors/download_media](hecat/processors/download_media.py)：使用 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 下载从 Shaarli 导入的书签的视频/音频文件
- [processors/url_check](hecat/processors/url_check.py)：检查数据中的死链接
- [processors/archive_webpages](hecat/processors/archive_webpages.py)：在本地归档网页

[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/Heg3Esg.png)](hecat/processors/url_check.py)
[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/RtiDE91.png)](hecat/processors/download_media.py)
[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/hecat-processor-github-metadata.png)](hecat/processors/github_metadata.py)

#### 导出器

将数据导出为其他格式：
- [exporters/markdown_singlepage](hecat/exporters/markdown_singlepage.py)：将数据渲染为单个 markdown 文档
- [exporters/markdown_multipage](hecat/exporters/markdown_multipage.py)：将数据渲染为可用于使用 Sphinx 生成 HTML 站点的多页 markdown 站点
- [exporters/html_table](hecat/exporters/html_table.py)：将数据渲染为单页 HTML 表格

[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/NvCOeiK.png)](hecat/exporters/markdown_singlepage.py)
[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/FFMPdaw.png)](hecat/exporters/html_table.py)
[![](https://gitlab.com/nodiscc/toolbox/-/raw/master/DOC/SCREENSHOTS/hecat-exporter-markdown-multipage.png)](hecat/exporters/markdown_multipage.py)


## 安装

```bash
# 安装依赖
sudo apt install python3-venv python3-pip
# 创建 python 虚拟环境
python3 -m venv ~/.venv
# 激活虚拟环境
source ~/.venv/bin/activate
# 安装程序
pip3 install git+https://gitlab.com/nodiscc/hecat.git
```

如需从本地副本安装：

```bash
# 获取副本
git clone https://gitlab.com/nodiscc/hecat.git
# 安装 python 包
cd hecat && python3 -m pip install .
```

要安装特定的[发行版](https://github.com/nodiscc/hecat/releases)，请调整 `git clone` 或 `pip3 install` 命令：

```bash
pip3 install git+https://gitlab.com/nodiscc/hecat.git@1.0.2
git clone -b 1.0.2 https://gitlab.com/nodiscc/hecat.git
```

## 使用方法

```bash
$ hecat --help
用法: hecat [-h] [--config CONFIG_FILE] [--log-level {ERROR,WARNING,INFO,DEBUG}]

可选参数:
  -h, --help            显示此帮助信息并退出
  --config CONFIG_FILE  配置文件（默认 .hecat.yml）
  --log-level {ERROR,WARNING,INFO,DEBUG} 日志级别（默认 INFO）
  --log-file LOG_FILE   日志文件（默认无）
```

如果未指定配置文件，则从当前目录中的 `.hecat.yml` 读取配置。


## 配置

hecat 执行配置文件中定义的所有步骤。对于每个步骤：

```yaml
steps:
  - name: 示例步骤 # 此步骤的任意名称
    module: processor/example # 要使用的模块，请参阅上面的模块列表
    module_options: # 特定于模块的选项字典，请参阅上面的模块列表
      option1: True
      option2: some_value
```

### 示例

#### Awesome 列表

从 [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) 的 markdown 列表格式导入数据：

```yaml
# .hecat.import.yml
# $ git clone https://github.com/awesome-selfhosted/awesome-selfhosted
# $ git clone https://github.com/awesome-selfhosted/awesome-selfhosted-data
steps:
  - name: 将 awesome-selfhosted README.md 导入到 YAML
    module: importers/markdown_awesome
    module_options:
      source_file: awesome-selfhosted/README.md
      output_directory: ./
      output_licenses_file: licenses.yml # 可选，默认 licenses.yml
      overwrite_tags: False # 可选，默认 False
```

根据 awesome-selfhosted 格式指南检查数据，导出为单页 markdown 和静态 HTML 站点（请参阅 [awesome-selfhosted-data](https://github.com/awesome-selfhosted/awesome-selfhosted-data)、其 [`Makefile`](https://github.com/awesome-selfhosted/awesome-selfhosted-data/blob/master/Makefile) 和 [Github Actions 工作流](https://github.com/awesome-selfhosted/awesome-selfhosted-data/tree/master/.github/workflows) 获取完整使用示例。请参阅 [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) 和 [awesome-selfhosted-html](https://github.com/nodiscc/awesome-selfhosted-html-preview/) 获取示例输出）：

```yaml
# .hecat.export.yml
steps:
  - name: 根据 awesome-selfhosted 指南检查数据
    module: processors/awesome_lint
    module_options:
      source_directory: awesome-selfhosted-data
      licenses_files:
        - licenses.yml
        - licenses-nonfree.yml

  - name: 将 YAML 数据导出为单页 markdown
    module: exporters/markdown_singlepage
    module_options:
      source_directory: awesome-selfhosted-data # 源/YAML 数据目录
      output_directory: awesome-selfhosted # 输出目录
      output_file: README.md # 输出 markdown 文件
      markdown_header: markdown/header.md # （可选，默认无）用作页眉的 markdown 文件路径（相对于 source_directory）
      markdown_footer: markdown/footer.md # （可选，默认无）用作页脚的 markdown 文件路径（相对于 source_directory）
      back_to_top_url: '#awesome-selfhosted' # （可选，默认 #）在"返回顶部"链接中使用的 URL/锚点
      exclude_licenses: # （可选，默认无）不要将具有这些许可证的软件项目写入输出文件
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

  - name: 将 YAML 数据导出为单页 markdown（non-free.md）
    module: exporters/markdown_singlepage
    module_options:
      source_directory: awesome-selfhosted-data
      output_directory: awesome-selfhosted
      output_file: non-free.md
      markdown_header: markdown/non-free-header.md
      licenses_file: licenses-nonfree.yml # （可选，默认 licenses.yml）从中加载许可证的 YAML 文件
      back_to_top_url: '##awesome-selfhosted---non-free-software'
      render_empty_categories: False # （可选，默认 True）不要渲染包含 0 个项目的类别
      render_category_headers: False # （可选，默认 True）不要渲染类别标题（描述、相关类别、外部链接...）
      include_licenses: # （可选，默认无）仅渲染至少匹配其中一个许可证的项目（不能与 exclude_licenses 一起使用）（按标识符）
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

  - name: 将 YAML 数据导出为多页 markdown/HTML 站点
    module: exporters/markdown_multipage
    module_options:
      source_directory: awesome-selfhosted-data # 包含 YAML 数据的目录
      output_directory: awesome-selfhosted-html # 要将 markdown 页面写入的目录
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

# $ sphinx-build -b html -c awesome-selfhosted-data/ awesome-selfhosted-html/md/ awesome-selfhosted-html/html/
# $ rm -r tests/awesome-selfhosted-html/html/.buildinfo tests/awesome-selfhosted-html/html/objects.inv awesome-selfhosted-html/html/.doctrees
```

<details><summary>使用 Github actions 的自动化示例：</summary>

```yaml
# .github/workflows/build.yml
jobs:
  build-markdown:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          ref: ${{ github.ref }}
      - run: python3 -m venv .venv && source .venv/bin/activate && pip3 install wheel && pip3 install --force git+https://github.com/nodiscc/hecat.git@1.2.0
      - run: source .venv/bin/activate && hecat --config .hecat/awesome-lint.yml
      - run: source .venv/bin/activate && hecat --config .hecat/export-markdown.yml

  build-html:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          ref: ${{ github.ref }}
      - run: python3 -m venv .venv && source .venv/bin/activate && pip3 install wheel && pip3 install --force git+https://github.com/nodiscc/hecat.git@1.2.0
      - run: source .venv/bin/activate && hecat --config .hecat/awesome-lint.yml
      - run: source .venv/bin/activate && hecat --config .hecat/export-html.yml
```
</details>

在重建 HTML/markdown 输出之前更新元数据：

```yaml
# .hecat.update_metadata.yml
steps:
  - name: 更新 github 项目元数据
    module: processors/github_metadata
    module_options:
      source_directory: awesome-selfhosted-data # 包含 YAML 数据和软件子目录的目录
      gh_metadata_only_missing: True # （默认 False）仅收集缺少 stargazers_count、updated_at、archived 之一的软件条目的元数据
      sleep_time: 7.3 # （默认 0）在每次请求 Github API 之前睡眠此时间
```

<details><summary>使用 Github actions 的自动化示例：</summary>

```yaml
# .github/workflows/update-metadata.yml
name: update metadata
on:
  schedule:
    - cron: '22 22 * * *'
  workflow_dispatch:

env:
  GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}

concurrency:
  group: update-metadata-${{ github.ref }}
  cancel-in-progress: true

jobs:
  update-metadata:
    if: github.repository == 'awesome-selfhosted/awesome-selfhosted-data'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python3 -m venv .venv && source .venv/bin/activate && pip3 install wheel && pip3 install --force git+https://github.com/nodiscc/hecat.git@1.2.0
      - run: source .venv/bin/activate && hecat --config .hecat/update-metadata.yml
      - name: commit and push changes
        run: |
          git config user.name awesome-selfhosted-bot
          git config user.email github-actions@github.com
          git add software/ tags/ platforms/ licenses*.yml
          git diff-index --quiet HEAD || git commit -m "[bot] update projects metadata"
          git push
  build:
    if: github.repository == 'awesome-selfhosted/awesome-selfhosted-data'
    needs: update-metadata
    uses: ./.github/workflows/build.yml
    secrets: inherit
```

</details>


检查死链接：

```yaml
# .hecat.url_check.yml
steps:
  - name: 检查 URL
    module: processors/url_check
    module_options:
      source_directories:
        - awesome-selfhosted-data/software
        - awesome-selfhosted-data/tags
      source_files:
        - awesome-selfhosted-data/licenses.yml
      errors_are_fatal: True
      exclude_regex:
        - '^https://github.com/[\w\.\-]+/[\w\.\-]+$' # 不检查将由 github_metadata 模块处理的 URL
        - '^https://retrospring.net/$' # DDoS 保护页面，总是返回 403
        - '^https://www.taiga.io/$' # 总是返回 403 Request forbidden by administrative rules
        - '^https://docs.paperless-ngx.com/$' # DDoS 保护页面，总是返回 403
        - '^https://demo.paperless-ngx.com/$' # DDoS 保护页面，总是返回 403
        - '^https://git.dotclear.org/dev/dotclear$' # DDoS 保护页面，总是返回 403
        - '^https://word-mastermind.glitch.me/$' # 演示实例启动时间较长，使用默认的 10s 超时会超时
        - '^https://getgrist.com/$' # hecat/python-requests 错误？'Received response with content-encoding: gzip,br, but failed to decode it.'
        - '^https://www.uvdesk.com/$' # DDoS 保护页面，总是返回 403
        - '^https://demo.uvdesk.com/$' # DDoS 保护页面，总是返回 403
        - '^https://notes.orga.cat/$' # DDoS 保护页面，总是返回 403
        - '^https://cytu.be$' # DDoS 保护页面，总是返回 403
        - '^https://demo.reservo.co/$' # hecat/python-requests 错误？总是返回 404 但网站在浏览器中正常工作
        - '^https://crates.io/crates/vigil-server$' # hecat/python-requests 错误？总是返回 404 但网站在浏览器中正常工作
        - '^https://nitter.net$' # 在 github actions 中总是超时，但网站在浏览器中正常工作
```

<details><summary>使用 Github actions 的自动化示例：</summary>

```yaml
# .github/workflows/url-check.yml
name: dead links

on:
  schedule:
    - cron: '22 22 * * *'
  workflow_dispatch:

env:
  GITHUB_TOKEN: ${{secrets.GITHUB_TOKEN}}

concurrency:
  group: dead-links-${{ github.ref }}
  cancel-in-progress: true

jobs:
  check-dead-links:
    if: github.repository == 'awesome-selfhosted/awesome-selfhosted-data'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python3 -m venv .venv && source .venv/bin/activate && pip3 install wheel && pip3 install --force git+https://github.com/nodiscc/hecat.git@1.2.0
      - run: source .venv/bin/activate && hecat --config .hecat/url-check.yml
```

</details>

#### Shaarli

从 Shaarli 实例导入数据，下载由特定标签标识的视频/音频文件，检查死链接，导出到单页 HTML 页面/表格：

```bash
# hecat 消费来自 https://github.com/shaarli/python-shaarli-client 的输出
# 安装 python API 客户端
python3 -m venv .venv && source .venv/bin/activate && pip3 install shaarli-client
# 编辑 python-shaarli-client 配置文件
mkdir -p ~/.config/shaarli/ && nano ~/.config/shaarli/client.ini
```
```ini
# ~/.config/shaarli/client.ini
[shaarli]
url = https://links.example.org
secret = AAAbbbZZZvvvSSStttUUUvvVXYZ
```
```bash
# 从您的 shaarli 实例下载数据
shaarli --outfile /path/to/shaarli-export.json get-links --limit=all
```
```yaml
# .hecat.yml
steps:
  - name: 从 shaarli API JSON 导入数据
      module: importers/shaarli_api
      module_options:
        source_file: /path/to/shaarli-export.json
        output_file: shaarli.yml
        skip_existing: True # （默认 True）跳过导入'url:'已存在于输出文件中的项目
        clean_removed: False # （默认 False）从输出文件中删除在输入文件中未找到'url:'的项目
        sort_by: created # （默认'created'）按此键对输出列表进行排序
        sort_reverse: True # （默认 True）按相反顺序对输出列表进行排序

  - name: 下载视频文件
      module: processors/download_media
      module_options:
        data_file: shaarli.yml # YAML 数据文件的路径
        only_tags: ['video'] # 仅下载标记有所有这些标签的项目
        exclude_tags: ['nodl'] # （默认 []），不下载标记有任何这些标签的项目
        output_directory: '/path/to/video/directory' # 媒体文件的输出目录路径
        download_playlists: False # （默认 False）下载播放列表
        skip_when_filename_present: True # （默认 True）当项目已经有'video_filename/audio_filename'键时跳过处理
        retry_items_with_error: True # （默认 True）重试之前记录错误的项目下载
        use_download_archive: True # （默认 True）使用 yt-dlp 存档文件记录已下载的项目，如果已经下载则跳过

  - name: 下载音频文件
    module: processors/download_media
    module_options:
      data_file: shaarli.yml
      only_tags: ['music']
      exclude_tags: ['nodl']
      output_directory: '/path/to/audio/directory'
      only_audio: True # （默认 False）下载'bestaudio'格式而不是默认的'best'

  - name: 检查 URL
    module: processors/url_check
    module_options:
      source_files:
        - shaarli.yml
      check_keys:
        - url
      errors_are_fatal: True
      exclude_regex:
        - '^https://www.youtube.com/watch.*$' # 不检查 youtube 视频 URL，即使对于不可用的视频也总是返回 HTTP 200```

  - name: 为标记为'hecat'或'doc'的项目存档网页
    module: processors/archive_webpages
    module_options:
      data_file: shaarli.yml
      only_tags: ['hecat', 'doc']
      exclude_tags: ['nodl']
      exclude_regex:
        - '^https://[a-z]\.wikipedia.org/wiki/.*$' # 不存档维基百科页面，我们已经有了来自 https://dumps.wikimedia.org/ 的维基百科转储的本地副本
      output_directory: webpages
      clean_removed: True
      clean_excluded: True

  - name: 将 shaarli 数据导出为 HTML 表格
    module: exporters/html_table
    module_options:
      source_file: shaarli.yml # 从中加载数据的文件
      output_file: index.html # （默认 index.html）输出 HTML 表格文件
      html_title: "Shaarli export - shaarli.example.org" # （默认 "hecat HTML export"）输出 HTML 标题
      description_format: paragraph # （details/paragraph，默认 details）将描述包装在 HTML details 标签中
```

必须安装 [ffmpeg](https://ffmpeg.org/) 以支持音频/视频转换。[jdupes](https://github.com/jbruchon/jdupes)、[soundalike](https://github.com/derat/soundalike) 和 [videoduplicatefinder](https://github.com/0x90d/videoduplicatefinder) 可能进一步帮助处理重复文件和媒体。


## 支持

请将任何问题提交到 <https://gitlab.com/nodiscc/hecat/-/issues> 或 <https://github.com/nodiscc/hecat/issues>


## 贡献

欢迎在 <https://gitlab.com/nodiscc/hecat/-/merge_requests> 或 <https://github.com/nodiscc/hecat/pulls> 提交错误报告、建议、代码清理、文档、测试、改进、对其他输入/输出格式的支持。


## 测试

```bash
# 安装 pyvenv、pip 和 make
$ sudo apt install python3-pip python3-venv make
# 使用 Makefile 运行测试
$ make help 
用法: make 目标
可用目标:
help                生成带有描述的目标列表
clean               清理通过 make install/test_run 生成的文件
install             安装在虚拟环境中
test                运行测试
test_short          运行测试，除了那些消耗 github API 请求/长 URL 检查的测试
test_pylint         运行 linter（非阻塞）
clone_awesome_selfhosted                克隆 awesome-selfhosted/awesome-selfhosted-data
test_import_awesome_selfhosted          测试从 awesome-sefhosted 导入
test_process_awesome_selfhosted         测试 awesome-selfhosted-data 上的所有处理步骤
test_url_check      测试 awesome-sefhosted-data 上的 URL 检查器
test_update_github_metadata             测试 awesome-selfhosted-data 上的 github 元数据更新器/处理器
test_awesome_lint   测试 awesome-sefhosted-data 上的 linter/合规性检查器
test_export_awesome_selfhosted_md       测试从 awesome-selfhosted-data 导出到单页 markdown
test_export_awesome_selfhosted_html     测试从 awesome-selfhosted-data 导出到单页 HTML
test_import_shaarli 测试从 shaarli JSON 导入
test_download_video 测试从 shaarli 导入下载视频，测试日志文件创建
test_download_audio 测试从 shaarli 导入下载音频文件
test_archive_webpages                   测试网页归档
test_export_html_table                  测试将 shaarli 数据导出为 HTML 表格
scan_trivy          运行 trivy 漏洞扫描器
```

## 许可证

[GNU GPLv3](LICENSE)
