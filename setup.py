#!/usr/bin/env python
from setuptools import setup
VERSION = '0.0.1'

setup(
    name='reformer',
    version=VERSION,
    py_modules=['reformer'],
    url='https://github.com/Krukov/reformer',
    download_url='https://github.com/Krukov/reformer/tarball/' + VERSION,
    license='MIT',
    author='Dmitry Krukov',
    author_email='glebov.ru@gmail.com',
    description='The tool for creating notes',
    long_description='',
    keywords='reformat format transform serializer schema',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules', 
    ],
)
