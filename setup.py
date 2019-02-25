import setuptools

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ntunnel-gparmeggiani",
    version="0.1.0",
    author="Giacomo Parmeggiani",
    author_email="giacomo.parmeggiani@gmail.com",
    description="Python implementation of Navicat's scripts for HTTP tunnelling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gparmeggiani/py-navicat-http-tunnel",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)