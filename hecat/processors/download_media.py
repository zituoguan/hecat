"""使用 yt-dlp 下载 `url` 键中的视频/音频
将下载的文件名写回原始数据文件的 'filename' 键中
支持的网站：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
必须安装 ffmpeg (https://ffmpeg.org/) 以支持音频/视频转换

# $ python3 -m venv .venv && source .venv/bin/activate && pip3 install shaarli-client && shaarli get-links --limit=all >| shaarli.json
# $ hecat --config tests/.hecat.import_shaarli.yml
# $ cat tests/.hecat.download_video.yml
steps:
  - name: 下载视频文件
    module: processors/download_media
    module_options:
      data_file: tests/shaarli.yml # YAML 数据文件的路径
      only_tags: ['video'] # 仅下载带有所有这些标签的项目
      exclude_tags: ['nodl'] # (默认 [])，不下载带有任何这些标签的项目
      output_directory: 'tests/video' # 媒体文件的输出目录路径
      download_playlists: False # (默认 False) 下载播放列表
      skip_when_filename_present: True # (默认 True) 当项目已有 'video_filename/audio_filename': 键时跳过处理
      retry_items_with_error: True # (默认 True) 重试之前记录了错误的项目下载
      only_audio: False # (默认 False) 下载 'bestaudio' 格式而不是默认的 'best'
      use_download_archive: True # (默认 True) 使用 yt-dlp 存档文件记录已下载的项目，如果已经下载则跳过

# $ cat tests/.hecat.download_audio.yml
steps:
  - name: 下载音频文件
    module: processors/download_media
    module_options:
      data_file: tests/shaarli.yml
      only_tags: ['music']
      exclude_tags: ['nodl']
      output_directory: 'tests/audio'
      only_audio: True

# $ hecat --config tests/.hecat.download_video.yml
# $ hecat --config tests/.hecat.download_audio.yml

数据文件格式（import_shaarli 模块的输出）：
# shaarli.yml
- id: 1667 # 必需，唯一标识
  url: https://www.youtube.com/watch?v=BaW_jenozKc # 必需，yt-dlp 支持的 URL
  tags:
    - tag1
    - tag2
    - video
    - music
  ...
  video_filename: 'Philipp_Hagemeister - youtube-dl_test_video_a - youtube-BaW_jenozKc.webm' # 自动添加

源目录结构：
└── shaarli.yml

输出目录结构：
└── tests/video/Philipp_Hagemeister - youtube-dl_test_video_a - youtube-BaW_jenozKc.webm
└── tests/video/Philipp_Hagemeister - youtube-dl_test_video_a - youtube-BaW_jenozKc.info.json
└── tests/video/Philipp_Hagemeister - youtube-dl_test_video_a - youtube-BaW_jenozKc.en.vtt
"""

import os
import logging
import ruamel.yaml
import yt_dlp
from ..utils import load_yaml_data, write_data_file

yaml = ruamel.yaml.YAML()
yaml.indent(sequence=2, offset=0)
yaml.width = 99999

def download_media(step):
    """从每个项目的 'url' 下载视频，如果它匹配 step['only_tags'] 中的一个，
    为每个下载的项目将下载的文件名写入原始数据文件中的新键 audio_filename/video_filename
    """
    # print(help(yt_dlp.YoutubeDL))
    ydl_opts = {
        'outtmpl': '%(uploader)s - %(title)s - %(extractor)s-%(id)s.%(ext)s',
        'trim_file_name': 180,
        'writeinfojson': True,
        'writesubtitles': True,
        'restrictfilenames': True,
        'compat_opts': ['no-live-chat'],
        'download_archive': 'yt-dlp.video.archive',
        'noplaylist': True
    }
    filename_key = 'video_filename'
    error_key = 'video_download_error'
    skipped_count = 0
    downloaded_count = 0
    error_count = 0
    # 当 only_audio = True 时添加特定选项
    if 'only_audio' in step['module_options'] and step['module_options']['only_audio']:
        ydl_opts['postprocessors'] =  [ {'key': 'FFmpegExtractAudio'} ]
        ydl_opts['keepvideo'] = False
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['download_archive'] = 'yt-dlp.audio.archive'
        filename_key = 'audio_filename'
        error_key = 'audio_download_error'
    ydl_opts['outtmpl'] = step['module_options']['output_directory'] + '/' + ydl_opts['outtmpl']
    ydl_opts['download_archive'] = step['module_options']['output_directory'] + '/' + ydl_opts['download_archive']
    if 'use_download_archive' in step['module_options'] and not step['module_options']['use_download_archive']:
        del ydl_opts['download_archive']
    if 'download_playlists' in step.keys() and step['download_playlists']:
        ydl_opts['noplaylist'] == False

    items = load_yaml_data(step['module_options']['data_file'])
    for item in items:
        # 当 skip_when_filename_present = True 且 video/audio_filename 键已存在时跳过下载
        if (('skip_when_filename_present' not in step['module_options'].keys() or
                step['module_options']['skip_when_filename_present']) and filename_key in item.keys()):
            logging.debug('跳过 %s (id %s): %s 已在数据文件中记录', item['url'], item['id'], filename_key)
            skipped_count = skipped_count +1
        # 当 retry_items_with_error = False 且 video/audio_download_error 键已存在时跳过下载
        elif ('retry_items_with_error' in step['module_options'] and
                not step['module_options']['retry_items_with_error'] and
                error_key in item.keys()):
            logging.debug('跳过 %s (id %s): 不重试带有 %s 设置的项目下载', item['url'], item['id'], error_key)
            skipped_count = skipped_count +1
        # 当项目的一个标签匹配 exclude_tags 中的标签时跳过下载
        elif ('exclude_tags' in step['module_options'] and
                any(tag in item['tags'] for tag in step['module_options']['exclude_tags'])):
            logging.debug('跳过 %s (id %s): 一个或多个标签存在于 exclude_tags 中', item['url'], item['id'])
            skipped_count = skipped_count +1
        # 如果 only_tags 中的所有标签都存在于项目的标签中，则下载
        elif list(set(step['module_options']['only_tags']) & set(item['tags'])):
            logging.info('正在下载 %s (id %s)', item['url'], item ['id'])
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(item['url'], download=True)
                    if info is not None:
                        # TODO 音频提取后无法获取真实的最终文件名 https://github.com/ytdl-org/youtube-dl/issues/5710, https://github.com/ytdl-org/youtube-dl/issues/7137
                        outpath = ydl.prepare_filename(info)
                        for item2 in items:
                            if item2['id'] == item['id']:
                                item2[filename_key] = outpath
                                item.pop(error_key, False)
                                break
                        write_data_file(step, items)
                    downloaded_count = downloaded_count +1
                except (yt_dlp.utils.DownloadError, AttributeError) as e:
                    logging.error('%s (id %s): %s', item['url'], item['id'], str(e))
                    item[error_key] = str(e)
                    write_data_file(step, items)
                    error_count = error_count + 1
        else:
            logging.debug('跳过 %s (id %s): 没有匹配 only_tags 的标签', item['url'], item['id'])
            skipped_count = skipped_count + 1
    logging.info('处理完成。已下载: %s - 已跳过: %s - 错误 %s', downloaded_count, skipped_count, error_count)
    