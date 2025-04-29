# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    # name of the package
    name='electrooptic', 
    
    # version of package
    version='0.1.0', 
    
    # package description
    description='electrooptic: simulation tool for optical modulators', 
    
    # author information
    author='Samuel Häusler', 
    url='https://github.com/samuehae/electrooptic', 
    
    # package license
    license='MIT', 
    
    # packages to process (build, distribute, install)
    packages=['electrooptic'], 
    
    # required packages
    install_requires=['numpy'], 
    extras_require={'examples': ['matplotlib'], }
)
