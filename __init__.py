# mei_tools/__init__.py
from .processor import MEI_Metadata_Updater
from .features import XMLProcessor

__package__ = __name__
__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = ['MEI_Metadata_Updater', 'XMLProcessor']