"""The setup module."""
import os

from setuptools import find_packages, setup

VERSION: str = "0.0.9"

# get the current path
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# construct the readme path
README_PATH = os.path.join(os.path.join(CURRENT_PATH, "docs"), "README.md")
# now construct the requirements path
REQS_PATH = os.path.join(CURRENT_PATH, "requirements_prod.txt")

# parse the readme into a variable
with open(README_PATH, "r", encoding="utf8") as rmd:
    long_desc = rmd.read()

# fetch the requirements required
with open(REQS_PATH, "r", encoding="utf8") as req_file:
    requirements = req_file.read().split("\n")


if __name__ == "__main__":
    setup(
        name="py-dspinlock",
        version=VERSION,
        author="Andreas A. Grammenos",
        author_email="ag926@cl.cam.ac.uk",
        description="A distributed spinlock for Python",
        long_description=long_desc,
        url="https://github.com/andylamp/py-dpspinlock/",
        packages=find_packages(),
        install_requires=requirements,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "License :: OSI Approved :: MIT License",
        ],
        license="MIT",
        license_files=("LICENSE",),
        python_requires=">=3.10",
        include_package_data=True,
        zip_safe=False,
    )
