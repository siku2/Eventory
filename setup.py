import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    "pip",
    "pythonnet",
    "pyyaml"
]

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
    packages=["eventory"],
    install_requires=requires
)
