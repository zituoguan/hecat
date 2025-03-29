SHELL := /bin/bash

.PHONY: help # 生成带描述的目标列表
help:
	@echo "用法: make 目标"
	@echo "可用目标:"
	@grep '^.PHONY: .* #' Makefile | sed 's/\.PHONY: \(.*\) # \(.*\)/\1	\2/' | expand -t20

.PHONY: clean # 清理由 make install/test_run 生成的文件
clean:
	-rm -rf build/ dist/ hecat.egg-info/ tests/awesome-selfhosted tests/awesome-selfhosted-data tests/audio/ tests/video/ tests/shaarli.yml tests/html-table hecat.log tests/awesome-selfhosted-html tests/requirements.txt trivy trivy_*_Linux-64bit.tar.gz tests/webpages/

# 不要从 setup.py/install_requires 安装 sphinx，这是针对 https://github.com/sphinx-doc/sphinx/issues/11130 的临时解决方案
.PHONY: install # 安装在虚拟环境中
install:
	python3 -m venv .venv && source .venv/bin/activate && \
	pip3 install wheel && \
	python3 -m pip install .

##### 测试 #####

.PHONY: test # 运行测试
test: test_pylint clean test_import_shaarli test_download_video test_download_audio test_export_html_table clone_awesome_selfhosted test_import_awesome_selfhosted test_process_awesome_selfhosted test_awesome_lint test_export_awesome_selfhosted_md test_export_awesome_selfhosted_html test_archive_webpages scan_trivy

.PHONY: test_short # 运行测试，除了那些消耗 github API 请求/长 URL 检查的测试
test_short: test_pylint clean test_import_shaarli test_archive_webpages test_download_video test_download_audio test_export_html_table clone_awesome_selfhosted test_awesome_lint test_export_awesome_selfhosted_md test_export_awesome_selfhosted_html

.PHONY: test_pylint # 运行 linter（非阻塞）
test_pylint: install
	source .venv/bin/activate && \
	pip3 install pylint pyyaml && \
	pylint --errors-only --disable=too-many-locals,line-too-long,consider-using-f-string hecat
	-source .venv/bin/activate && \
	pylint --disable=too-many-locals,line-too-long,consider-using-f-string hecat

.PHONY: clone_awesome_selfhosted # 克隆 awesome-selfhosted/awesome-selfhosted-data
clone_awesome_selfhosted:
	git clone --depth=1 https://github.com/awesome-selfhosted/awesome-selfhosted tests/awesome-selfhosted
	git clone https://github.com/awesome-selfhosted/awesome-selfhosted-data tests/awesome-selfhosted-data

.PHONY: test_import_awesome_selfhosted # 测试从 awesome-sefhosted 导入
test_import_awesome_selfhosted: install
	rm -rf tests/awesome-selfhosted-data/{tags,software,platforms}
	mkdir tests/awesome-selfhosted-data/{tags,software,platforms}
	source .venv/bin/activate && \
	hecat --config tests/.hecat.import_awesome_selfhosted.yml && \
	hecat --config tests/.hecat.import_awesome_selfhosted_nonfree.yml

.PHONY: test_process_awesome_selfhosted # 测试 awesome-selfhosted-data 上的所有处理步骤
test_process_awesome_selfhosted: install test_url_check test_update_github_metadata test_awesome_lint
	cd tests/awesome-selfhosted-data && git --no-pager diff --color=always

.PHONY: test_url_check # 在 awesome-sefhosted-data 上测试 URL 检查器
test_url_check: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.url_check.yml

.PHONY: test_update_github_metadata # 在 awesome-selfhosted-data 上测试 github 元数据更新器/处理器
test_update_github_metadata: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.github_metadata.yml

.PHONY: test_awesome_lint # 在 awesome-sefhosted-data 上测试 linter/合规性检查器
test_awesome_lint: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.awesome_lint.yml

.PHONY: test_export_awesome_selfhosted_md # 测试从 awesome-selfhosted-data 导出到单页 markdown
test_export_awesome_selfhosted_md: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.export_markdown_singlepage.yml && \
	cd tests/awesome-selfhosted && git --no-pager diff --color=always

.PHONY: test_export_awesome_selfhosted_html # 测试从 awesome-selfhosted-data 导出到单页 HTML
test_export_awesome_selfhosted_html: install
	rm -rf tests/awesome-selfhosted-html
	mkdir -p tests/awesome-selfhosted-html
	source .venv/bin/activate && \
	hecat --config tests/.hecat.export_markdown_multipage.yml && \
	sed -i 's|<a href="https://github.com/pradyunsg/furo">Furo</a>|<a href="https://github.com/nodiscc/hecat/">hecat</a>, <a href="https://www.sphinx-doc.org/">sphinx</a> and <a href="https://github.com/pradyunsg/furo">furo</a>. Content under <a href="https://github.com/awesome-selfhosted/awesome-selfhosted-data/blob/master/LICENSE">CC-BY-SA 3.0</a> license.|' .venv/lib/python*/site-packages/furo/theme/furo/page.html && \
	sphinx-build -b html -c tests/ -d tests/awesome-selfhosted-html/.doctrees tests/awesome-selfhosted-html/md/ tests/awesome-selfhosted-html/html/
	# 移除用于静态站点发布的未使用文件
	rm tests/awesome-selfhosted-html/html/.buildinfo tests/awesome-selfhosted-html/html/objects.inv

.PHONY: test_import_shaarli # 测试从 shaarli JSON 导入
test_import_shaarli: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.import_shaarli.yml

.PHONY: test_download_video # 测试从 shaarli 导入下载视频，测试日志文件创建
test_download_video: install
	rm -f tests/hecat.log
	source .venv/bin/activate && \
	hecat --log-file tests/hecat.log --config tests/.hecat.download_video.yml
	grep -q 'writing data file tests/shaarli.yml' tests/hecat.log

.PHONY: test_download_audio # 测试从 shaarli 导入下载音频文件
test_download_audio: install
	source .venv/bin/activate && \
	hecat --config tests/.hecat.download_audio.yml

.PHONY: test_archive_webpages # 测试网页归档
test_archive_webpages: install
	mkdir -p tests/webpages
	# 创建应该被 clean_removed 移除的目录
	mkdir -p tests/webpages/public/9999999999
	source .venv/bin/activate && \
	hecat --log-level DEBUG --config tests/.hecat.archive_webpages.yml
	# 测试归档页面的存在和内容
	@grep -q 'Template Designer Documentation' tests/webpages/public/8351/jinja.palletsprojects.com/en/latest/templates/index.html
	# 测试目录是否被有效移除
	@if [[ -d tests/webpages/public/9999999999 ]]; then echo "错误 tests/webpages/public/9999999999 应该已被 clean_removed: True 移除"; exit 1; fi
	@if [[ -d tests/webpages/public/6625 ]]; then echo "错误 tests/webpages/public/6625 应该已被 clean_excluded: True 移除"; exit 1; fi


.PHONY: test_export_html_table # 测试将 shaarli 数据导出为 HTML 表格
test_export_html_table: install
	mkdir -p tests/html-table
	source .venv/bin/activate && \
	hecat --config tests/.hecat.export_html_table.yml

TRIVY_VERSION=0.44.0
TRIVY_EXIT_CODE=1
.PHONY: scan_trivy # 运行 trivy 漏洞扫描器
scan_trivy:
	source .venv/bin/activate && pip3 freeze --local > tests/requirements.txt
	wget --quiet --continue -O trivy_$(TRIVY_VERSION)_Linux-64bit.tar.gz https://github.com/aquasecurity/trivy/releases/download/v$(TRIVY_VERSION)/trivy_$(TRIVY_VERSION)_Linux-64bit.tar.gz
	tar -z -x trivy -f trivy_$(TRIVY_VERSION)_Linux-64bit.tar.gz
	./trivy --exit-code $(TRIVY_EXIT_CODE) fs tests/requirements.txt
	