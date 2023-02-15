import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="MTGScrapper",
    version="0.0.1",
    author="Axel Mendoza",
    author_email="axel.mendoza@epita.fr",
    description=("A package that scraps Magic The Gathering content on the internet."),
    license="BSD",
    packages=['mtgscrapper'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ]
)
