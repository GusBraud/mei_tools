# mei_tools/__init__.py
from .mei_music_feature_processor import MEI_Music_Feature_Processor
from .mei_metadata_processor import MEI_Metadata_Updater

python setup.py sdist bdist_wheel
python -m build

__package__ = __name__
__version__ = "2.0.2"
__author__ = "Richard Freedman"