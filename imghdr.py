"""
簡化版本的 imghdr 模組，用於檢測圖像文件類型。
"""

__all__ = ["what"]

def what(file, h=None):
    """
    檢測圖像類型。
    
    參數:
        file: 文件名或文件對象
        h: 可選的文件頭
        
    返回:
        圖像類型字符串，或 None 如果檢測失敗
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    if h.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'WEBP'):
        return 'webp'
    return None

tests = [] 