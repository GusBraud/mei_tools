# setup.py
from setuptools import setup, find_packages

setup(
    name='meitools',
    version='1.0.0',
    description='MEI file processing tools',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/your-username/mei-tools',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'lxml',
        'pathlib'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)