# 变更日志

本项目的所有重要变更都将记录在此文件中。
格式基于 [Keep a Changelog](http://keepachangelog.com/)。

#### [v1.4.0](https://github.com/nodiscc/hecat/releases/tag/1.4.0) - 未发布

**新增：**
- processors/archive_webpages: 允许使用 `exclude_regex: URL_REGEX` 排除 URL
- processors/archive_webpages: 允许移除已经存在的被排除 URL 的本地归档（`clean_excluded: False/True`）

---------------------

#### [v1.3.1](https://github.com/nodiscc/hecat/releases/tag/1.3.1) - 2024-12-29

**修复：**
- utils: to_kebab_case(): 从文件名中删除在 MS Windows 上无效的字符

---------------------

#### [v1.3.0](https://github.com/nodiscc/hecat/releases/tag/1.3.0) - 2024-12-26

**新增：**
- 添加 [archive_webpages](hecat/processors/archive_webpages.py) 处理器（下载项目中 `url` 键中链接的网页的本地副本）
- processors/awesome_lint: 检查 `software/*` 中的文件名是否与每个文件内的 `name:` 属性的 kebab-case 版本匹配
- processors/awesome_lint: 通过 `platforms_required_fields` 模块选项（默认为 `['description']`）使 `platforms` 的必填字段/属性列表可配置

**更改：**
- processors/awesome_lint: 检查 `depends_3rdparty` 是否为有效的布尔值（`true/false/True/False`）
- exporters/html_table: 添加一列显示页面本地归档的链接（如由 `processors/archive_webpages` 生成），当页面归档失败时在此列中写入警告符号
- exporters/html_table: 自动从 URL 创建链接
- exporters/html_table: 将标题/描述列宽限制在 480px 到 900px 之间
- exporters/html_table: 重新排序列
- 更新文档

**修复：**
- html_table: 修复围栏代码块的格式

---------------------

#### [v1.2.2](https://github.com/nodiscc/hecat/releases/tag/1.2.2) - 2023-11-03

**更改：**
- processors/github_metadata: 使用 git 提交日期而不是作者日期

---------------------

#### [v1.2.1](https://github.com/nodiscc/hecat/releases/tag/1.2.1) - 2023-10-27

**新增：**
- processors/awesome_lint: 允许通过 `source_code_url` 跳过特定项目的最后更新检查

**修复：**
- exporters/markdown_multipage: 在文字 HTML 块中对链接 `href` 进行 URL 编码
- processors/awesome_lint: 不要重复记录最后更新日期检查错误

---------------------

#### [v1.2.0](https://github.com/nodiscc/hecat/releases/tag/1.2.0) - 2023-10-10

**新增：**
- exporters/markdown_multipage: 为每个 `platform` 渲染子页面

**更改：**
- exporters/markdown_multipage: 将 CSS 样式移动到外部 CSS 文件。**现在 sphinx 配置文件中需要 `html_css_files = ['custom.css']`**
- processors/awesome_lint: 检查 `software` 项目中的 `platforms` 是否存在于主要 `platforms` 列表中
- processors/awesome_lint: 检查 `platform` 项目是否具有非空的 `description` 属性
- exporters/markdown_multipage: 防止 `platforms` 页面出现在 sphinx 搜索结果中

**修复：**
- exporters/markdown_multipage: 修复标签跨度周围的间距

---------------------


#### [v1.1.3](https://github.com/nodiscc/hecat/releases/tag/1.1.3) - 2023-09-19

**修复：**
- exporters/markdown_multipage: 修复客户端和演示链接前/之间/后的间距/换行

---------------------

#### [v1.1.2](https://github.com/nodiscc/hecat/releases/tag/1.1.2) - 2023-09-19

**更改：**
- processors/awesome_lint: 在对 `software` 项目进行检查之前对 `tag` 项目运行检查

**修复：**
- processors/awesome_lint: 修复当标签项目少于 N 个时 `redirect` 属性的检测
- processors/awesome_lint: 如果 `items_in_redirect_fatal: True`（默认值），则当任何 `software` 项目引用具有设置/非空 `redirect:` 的 `tag` 时失败
- processors/awesome_lint: 如果任何 `tag` 项目被引用的 `software` 项目少于 3 个，除非其 `redirect` 属性已设置/非空，否则失败
- exporters/markdown_multipage: 为设置了 `demo_url` 的 `software` 项目渲染演示链接

---------------------


#### [v1.1.1](https://github.com/nodiscc/hecat/releases/tag/1.1.1) - 2023-08-19

**修复：**
- processors/awesome_lint: 修复错误级别消息中显示的 `older than ... days` 天数
- processors/github_metadata: 不要在 YAML 输出中分割长行

---------------------

#### [v1.1.0](https://github.com/nodiscc/hecat/releases/tag/1.1.0) - 2023-07-29

**新增：**
- processors/awesome_lint: 允许配置项目没有更新的天数，以触发信息/警告/错误消息（`last_updated_{error,warn,info}_days`，默认分别为 3650、365、186）

---------------------

#### [v1.0.2](https://github.com/nodiscc/hecat/releases/tag/1.0.2) - 2023-07-27

**更改：**
- 依赖项: 升级 sphinx 到 v7.1.0，将 furo 固定到 v2023.7.26

**修复：**
- doc/tests: 不要使用已弃用的 `python3 setup.py install`，使用 `python3 -m pip install .`
- 依赖项: 通过 `install_requires` 安装 sphinx，不再需要单独的手动安装步骤

---------------------

#### [v1.0.1](https://github.com/nodiscc/hecat/releases/tag/1.0.1) - 2023-07-24

**更改：**
- utils: `to_kebab_case()`: 将 `:` 字符替换为 `-`（避免 NTFS 上的文件名问题，与自动锚点生成一致）

---------------------

#### [v1.0.0](https://github.com/nodiscc/hecat/releases/tag/1.0.0) - 2023-07-24

初始版本，请参阅 [README.md](https://github.com/nodiscc/hecat/blob/1.0.0/README.md) 和每个模块的 docstring 中的模块特定文档。
