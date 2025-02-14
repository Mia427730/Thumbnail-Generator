from .thumbnail_generator import ThumbnailGenerator

def classFactory(iface):
    return ThumbnailGenerator(iface)
