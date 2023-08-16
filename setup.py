import setuptools

with open("README.md", "rt", encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="carrot-shell",
    version="0.1.0",
    author="blueloveTH",
    author_email="blueloveth@foxmail.com",
    description="Carrot shell🥕 is the best shell in python, for developers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blueloveTH/ct-sh",
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)