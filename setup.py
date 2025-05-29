# setup.py
from setuptools import setup, find_packages

setup(
    name='config_manager',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pyyaml',
        'pytest'  # 仅用于测试
    ],
    author='Tony Xiao',
    author_email='tony.xiao@gmail.com',
    description='A robust configuration manager with auto-save feature',
    url='https://github.com/jaried/config_manager',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)