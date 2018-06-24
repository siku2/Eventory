import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    "aiohttp",
    "pip",
    "pyyaml",
    "yarl"
]

dependency_links = [
    "git+https://github.com/Rapptz/discord.py/tree/rewrite#egg=discord.py-1.0.0"
]

extras_require = {
    "ink": ["pythonnet"],
    "discord": ["discord.py"]
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
    packages=["eventory", "eventory.ext.discord", "eventory.ext.inktory"],
    install_requires=requires,
    extras_require=extras_require,
    dependency_links=dependency_links,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6"
    ]
)
