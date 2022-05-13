import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    "opentele",
    "telethon",
    "pyrogram",
    "tgcrypto",
    "stream-sqlite==0.0.38"

]

setuptools.setup(
    name="TGSessionsCoverter",
    version="0.0.2",
    author="watdev",
    author_email="v.liubachevskyi@gmail.com",
    description="This module is small util for converting Telegram sessions  to various formats (Telethon, Pyrogram, Tdata)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wathipol/TGSessionsCoverter",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
