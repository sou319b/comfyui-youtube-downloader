"""
YouTube動画ダウンロードノード
yt-dlpを使用してYouTube動画をダウンロードする
"""

import os
import re
import yt_dlp
from pathlib import Path


class YouTubeDownloaderNode:
    """
    YouTube動画をダウンロードするノード
    URLを受け取り、ComfyUIのoutputディレクトリに保存
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        """
        ノードの入力を定義
        """
        return {
            "required": {
                "video_url": ("STRING", {
                    "multiline": False,
                    "default": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                }),
                "download_type": (["video", "audio"], {
                    "default": "video"
                }),
                "video_type": (["通常動画", "ショート動画"], {
                    "default": "通常動画"
                }),
                "resolution": (["1080p", "720p", "480p", "360p"], {
                    "default": "720p"
                }),
                "video_format": (["mp4", "webm", "mkv"], {
                    "default": "mp4"
                }),
                "audio_format": (["mp3", "m4a", "opus", "wav"], {
                    "default": "mp3"
                }),
            },
            "optional": {
                "custom_filename": ("STRING", {
                    "multiline": False,
                    "default": ""
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "download_video"
    CATEGORY = "YouTube Downloader"
    OUTPUT_NODE = True
    
    def download_video(self, video_url, download_type="video", video_type="通常動画", resolution="720p", video_format="mp4", audio_format="mp3", custom_filename=""):
        """
        YouTube動画をダウンロードする関数
        """
        try:
            # ComfyUIのoutputディレクトリを取得
            # ComfyUIのルートディレクトリを見つける
            current_dir = Path(__file__).parent
            while current_dir.parent != current_dir:
                if (current_dir / "output").exists():
                    output_dir = current_dir / "output"
                    break
                current_dir = current_dir.parent
            else:
                # outputディレクトリが見つからない場合、現在のディレクトリに作成
                output_dir = Path(__file__).parent / "output"
                output_dir.mkdir(exist_ok=True)
            
            # ファイル名に使用できない文字を除去する関数
            def sanitize_filename(filename):
                # Windows/Linuxで使用できない文字を除去
                sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
                # 連続するアンダースコアを1つに
                sanitized = re.sub(r'_+', '_', sanitized)
                # 前後の空白やピリオドを除去
                sanitized = sanitized.strip('. ')
                return sanitized
            
            # 新しいサイズ指定フォーマット選択
            def create_format_selector(download_type, video_type, resolution, video_format, audio_format):
                if download_type == "audio":
                    # 音声のみダウンロード
                    if audio_format == "mp3":
                        return "bestaudio[ext=m4a]/bestaudio/best"
                    else:
                        return f"bestaudio[ext={audio_format}]/bestaudio/best"
                else:
                    # 解像度文字列を実際のピクセルサイズに変換
                    resolution_map = {
                        "1080p": (1920, 1080),
                        "720p": (1280, 720),
                        "480p": (854, 480),
                        "360p": (640, 360)
                    }
                    
                    # 目標サイズを決定
                    width, height = resolution_map.get(resolution, (1280, 720))
                    
                    # ショート動画の場合、縦横を逆転
                    if video_type == "ショート動画":
                        width, height = height, width  # 縦横逆転
                        print(f"[YouTube Downloader] Short video mode: target {width}x{height}")
                    else:
                        print(f"[YouTube Downloader] Normal video mode: target {width}x{height}")
                    
                    # サイズに基づくフォーマット選択（厳密なサイズマッチング）
                    # 1. 正確なサイズ
                    # 2. 同じまたは少し大きいサイズ
                    # 3. 少し小さいサイズ
                    # 4. フォールバック
                    
                    format_selector = f"""
                    bestvideo[width={width}][height={height}][ext={video_format}]+bestaudio[ext=m4a]/
                    bestvideo[width={width}][height={height}]+bestaudio/
                    bestvideo[width>={width}][height>={height}][width<={width+100}][height<={height+100}][ext={video_format}]+bestaudio[ext=m4a]/
                    bestvideo[width>={width}][height>={height}][width<={width+100}][height<={height+100}]+bestaudio/
                    bestvideo[width<={width}][height<={height}][width>={width-200}][height>={height-200}][ext={video_format}]+bestaudio[ext=m4a]/
                    bestvideo[width<={width}][height<={height}][width>={width-200}][height>={height-200}]+bestaudio/
                    bestvideo[height={height}][ext={video_format}]+bestaudio/
                    bestvideo[height<={height}][height>={height-200}][ext={video_format}]+bestaudio/
                    bestvideo[height<={height}][ext={video_format}]+bestaudio/
                    best[ext={video_format}]/
                    best
                    """.replace('\n', '').replace(' ', '')
                    
                    return format_selector
            
            format_selector = create_format_selector(download_type, video_type, resolution, video_format, audio_format)
            
            # yt-dlpの設定
            ydl_opts = {
                'format': format_selector,
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'noplaylist': True,
                'extract_flat': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'merge_output_format': video_format if download_type == "video" else None,
            }
            
            # 動画ダウンロードの場合、指定フォーマットに確実に変換
            if download_type == "video":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': video_format,
                }]
            
            # 音声ダウンロードの場合、postprocessorを追加
            if download_type == "audio":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format if audio_format != 'mp3' else 'mp3',
                    'preferredquality': '320' if audio_format == 'mp3' else 'best',
                }]
                
                # MP3以外の場合、追加設定
                if audio_format in ['wav', 'opus']:
                    ydl_opts['postprocessors'][0]['preferredquality'] = 'best'
            
            print(f"[YouTube Downloader] Extracting video info...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 動画情報を取得
                info = ydl.extract_info(video_url, download=False)
                video_title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')
                
                print(f"[YouTube Downloader] Found: {video_title}")
                print(f"[YouTube Downloader] Uploader: {uploader}")
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    print(f"[YouTube Downloader] Duration: {minutes}m{seconds}s")
                
                # Video info
                width = info.get('width', 0)
                height = info.get('height', 0)
                print(f"[YouTube Downloader] Original size: {width}x{height}")
                print(f"[YouTube Downloader] Video type: {video_type}")
                print(f"[YouTube Downloader] Target resolution: {resolution}")
                
                # Available formats
                formats = info.get('formats', [])
                print(f"[YouTube Downloader] Available formats: {len(formats)}")
                
                # Display available resolutions
                resolutions = {}
                for fmt in formats:
                    fmt_height = fmt.get('height')
                    fmt_width = fmt.get('width')
                    if fmt_height and fmt_width:
                        res_key = f"{fmt_width}x{fmt_height}"
                        if res_key not in resolutions:
                            resolutions[res_key] = []
                        resolutions[res_key].append(fmt.get('format_id', 'unknown'))
                
                print(f"[YouTube Downloader] Available resolutions:")
                for res, fmt_ids in sorted(resolutions.items(), key=lambda x: int(x[0].split('x')[1]), reverse=True):
                    print(f"[YouTube Downloader]   {res}: {len(fmt_ids)} formats")
                
                # 目標サイズに関する情報
                resolution_map = {
                    "1080p": (1920, 1080),
                    "720p": (1280, 720),
                    "480p": (854, 480),
                    "360p": (640, 360)
                }
                target_width, target_height = resolution_map.get(resolution, (1280, 720))
                
                if video_type == "ショート動画":
                    actual_target_width, actual_target_height = target_height, target_width
                    print(f"[YouTube Downloader] Target size (Short): {actual_target_width}x{actual_target_height}")
                else:
                    actual_target_width, actual_target_height = target_width, target_height
                    print(f"[YouTube Downloader] Target size (Normal): {actual_target_width}x{actual_target_height}")
                
                # Show matching formats
                print(f"[YouTube Downloader] Matching formats:")
                matching_formats = []
                for fmt in formats:
                    fmt_height = fmt.get('height', 0)
                    fmt_width = fmt.get('width', 0)
                    fmt_ext = fmt.get('ext', 'unknown')
                    fmt_id = fmt.get('format_id', 'unknown')
                    if fmt_height and fmt_width:
                        if (abs(fmt_width - actual_target_width) <= 200 and 
                            abs(fmt_height - actual_target_height) <= 200):
                            matching_formats.append(f"ID:{fmt_id} {fmt_width}x{fmt_height} {fmt_ext}")
                
                for fmt in matching_formats[:5]:
                    print(f"[YouTube Downloader]   {fmt}")
                
                # Format selector
                print(f"[YouTube Downloader] Format selector: {format_selector[:100]}...")
                
                # カスタムファイル名が指定されている場合
                if custom_filename.strip():
                    filename = sanitize_filename(custom_filename.strip())
                    ydl_opts['outtmpl'] = str(output_dir / f'{filename}.%(ext)s')
                    print(f"[YouTube Downloader] Using custom filename: {filename}")
                else:
                    sanitized_title = sanitize_filename(video_title)
                    ydl_opts['outtmpl'] = str(output_dir / f'{sanitized_title}.%(ext)s')
                    print(f"[YouTube Downloader] Using video title as filename")
                
                print(f"[YouTube Downloader] Starting {download_type} download...")
                print(f"[YouTube Downloader] Resolution: {resolution}")
                print(f"[YouTube Downloader] Type: {video_type}")
                if download_type == "video":
                    print(f"[YouTube Downloader] Format: {video_format}")
                    print(f"[YouTube Downloader] Post-processor: FFmpegVideoConvertor -> {video_format}")
                else:
                    print(f"[YouTube Downloader] Audio format: {audio_format}")
                
                # 新しい設定でダウンロード実行
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                    # ダウンロード前に最終的に選択される形式を確認
                    selected_info = ydl_download.extract_info(video_url, download=False)
                    if 'requested_formats' in selected_info:
                        print(f"[YouTube Downloader] Selected formats:")
                        for i, fmt in enumerate(selected_info['requested_formats']):
                            fmt_width = fmt.get('width', 'unknown')
                            fmt_height = fmt.get('height', 'unknown')
                            fmt_id = fmt.get('format_id', 'unknown')
                            fmt_ext = fmt.get('ext', 'unknown')
                            print(f"[YouTube Downloader]   {i+1}: ID={fmt_id} {fmt_width}x{fmt_height} {fmt_ext}")
                    elif 'width' in selected_info and 'height' in selected_info:
                        fmt_width = selected_info.get('width', 'unknown')
                        fmt_height = selected_info.get('height', 'unknown')
                        fmt_id = selected_info.get('format_id', 'unknown')
                        fmt_ext = selected_info.get('ext', 'unknown')
                        print(f"[YouTube Downloader] Selected: ID={fmt_id} {fmt_width}x{fmt_height} {fmt_ext}")
                    else:
                        print(f"[YouTube Downloader] Warning: Could not get format details")
                    
                    # 目標サイズと実際の選択をチェック
                    resolution_map = {
                        "1080p": (1920, 1080),
                        "720p": (1280, 720),
                        "480p": (854, 480),
                        "360p": (640, 360)
                    }
                    target_width, target_height = resolution_map.get(resolution, (1280, 720))
                    
                    if video_type == "ショート動画":
                        actual_target_width, actual_target_height = target_height, target_width
                    else:
                        actual_target_width, actual_target_height = target_width, target_height
                        
                    if 'requested_formats' in selected_info:
                        for fmt in selected_info['requested_formats']:
                            fmt_width = fmt.get('width')
                            fmt_height = fmt.get('height')
                            if fmt_width and fmt_height:
                                # サイズの一致度をチェック
                                width_diff = abs(fmt_width - actual_target_width)
                                height_diff = abs(fmt_height - actual_target_height)
                                if width_diff <= 50 and height_diff <= 50:
                                    print(f"[YouTube Downloader] ✅ Target size matched: {fmt_width}x{fmt_height}")
                                else:
                                    print(f"[YouTube Downloader] ⚠️ Size mismatch: {fmt_width}x{fmt_height} (target: {actual_target_width}x{actual_target_height})")
                                break
                    
                    ydl_download.download([video_url])
                
                # ダウンロードされたファイルのパスを取得
                if download_type == "audio":
                    # 音声ファイルの拡張子
                    file_ext = audio_format
                else:
                    # 動画ファイルの拡張子
                    file_ext = video_format
                
                if custom_filename.strip():
                    download_path = output_dir / f'{sanitize_filename(custom_filename.strip())}.{file_ext}'
                else:
                    download_path = output_dir / f'{sanitize_filename(video_title)}.{file_ext}'
                
                # ファイルが実際に存在するかチェック（拡張子が異なる場合があるため）
                if not download_path.exists():
                    # パターンマッチングで実際のファイルを探す
                    base_name = download_path.stem
                    for file in output_dir.glob(f"{base_name}.*"):
                        if download_type == "audio":
                            if file.suffix in ['.mp3', '.m4a', '.opus', '.wav', '.aac']:
                                download_path = file
                                break
                        else:
                            if file.suffix in ['.mp4', '.webm', '.mkv', '.avi', '.mov']:
                                download_path = file
                                break
                
                # ファイルサイズを取得
                file_size = ""
                if download_path.exists():
                    size_bytes = download_path.stat().st_size
                    if size_bytes > 1024 * 1024:  # MB
                        file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                    else:  # KB
                        file_size = f"{size_bytes / 1024:.1f} KB"
                
                # 動画タイプの絵文字
                type_emoji = "🎵" if download_type == "audio" else "🎬"
                type_name = "音声" if download_type == "audio" else "動画"
                
                # 実際のファイル拡張子を取得
                actual_format = download_path.suffix.lstrip('.') if download_path.exists() else "unknown"
                format_info = f"{audio_format} (実際: {actual_format})" if download_type == "audio" else f"{video_format} (実際: {actual_format})"
                
                # 動画タイプ情報
                type_info = f"📱 {video_type}" if video_type == "ショート動画" else f"🖥️ {video_type}"
                resolution_map = {
                    "1080p": (1920, 1080),
                    "720p": (1280, 720),
                    "480p": (854, 480),
                    "360p": (640, 360)
                }
                target_width, target_height = resolution_map.get(resolution, (1280, 720))
                
                if video_type == "ショート動画":
                    final_target_size = f"{target_height}x{target_width}"
                else:
                    final_target_size = f"{target_width}x{target_height}"
                
                # 統合結果メッセージを作成
                result_message = f"""{type_emoji} YouTube{type_name}ダウンロード完了！

📹 タイトル: {video_title}
👤 アップロード者: {uploader}
⏱️ 長さ: {minutes}分{seconds}秒
{type_info}
📏 解像度: {resolution} ({final_target_size})
📁 保存先: {str(download_path)}
📐 ファイルサイズ: {file_size}
📦 形式: {format_info}
✅ ステータス: ダウンロード成功

指定された{video_type}の{final_target_size}サイズで{type_name}がComfyUI の output ディレクトリに保存されました。
このノードは単体で完結しており、他のノードに接続する必要はありません。"""

                print(f"[YouTube Downloader] Download complete: {video_title}")
                print(f"[YouTube Downloader] Saved to: {str(download_path)}")
                
                return (result_message,)
                
        except Exception as e:
            error_message = f"""❌ YouTube動画ダウンロードエラー

🔗 URL: {video_url}
💥 エラー内容: {str(e)}

以下をご確認ください：
• URLが正しいかどうか
• インターネット接続
• yt-dlp ライブラリがインストールされているか
• 動画が利用可能かどうか"""

            print(f"[YouTube Downloader] Error: {str(e)}")
            
            return (error_message,)


# ComfyUIに登録するためのマッピング
NODE_CLASS_MAPPINGS = {
    "YouTubeDownloaderNode": YouTubeDownloaderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YouTubeDownloaderNode": "YouTube 動画ダウンローダー"
}
