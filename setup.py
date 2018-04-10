import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    "aiohttp",
    "pip",
    "pythonnet",
    "pyyaml",
    "yarl"
]

extras_require = {
    "ink": ["pycparser", "pythonnet"],
    "discord": ["https://github.com/Rapptz/discord.py/archive/rewrite.zip"]
}

about = {}
with open(os.path.join(here, "eventory", "__version__.py"), "r") as f:
    exec(f.read(), about)

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    url=about["__url__"],
    author=about["__author__"],
    author_email=about["__author_email__"],
    license=about["__license__"],
    packages=["eventory", "eventory.ext"],
    install_requires=requires,
    extras_require=extras_require,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6"
    ]
)
