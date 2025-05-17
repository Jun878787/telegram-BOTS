"""
Recognize image file formats based on their first few bytes.

This is a simplified version of the imghdr module to address import issues.
"""

__all__ = ["what"]

def what(file, h=None):
    """
    Recognize the type of an image file.
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            try:
                location = file.tell()
                h = file.read(32)
                file.seek(location)
            except (AttributeError, OSError):
                return None
    
    # JPEG
    if h[0:2] == b'\xff\xd8':
        return 'jpeg'
    
    # PNG
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    
    # GIF
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    
    # TIFF
    if h[0:2] in (b'MM', b'II'):
        return 'tiff'
    
    # WebP
    if h[0:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    
    return None 