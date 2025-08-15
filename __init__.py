"""
YouTube Downloader Node for ComfyUI
Download YouTube videos and audio with precision control
"""

from .youtube_downloader_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# ComfyUIに認識させるためのエクスポート
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
