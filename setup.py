from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fileorganizer",
    version="1.1.0",
    author="merknu",
    author_email="merknu@github.com",
    description="An automated file organization tool with GUI support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/merknu/FileOrganizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment :: File Managers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "watchdog>=2.1.0",
        "Pillow>=10.0.0",
        "mutagen>=1.46.0",
        "python-magic>=0.4.27",
        "pypdf>=3.17.0",
        "python-docx>=0.8.11",
        "moviepy>=1.0.3",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "fileorganizer=main:main",
        ],
        "gui_scripts": [
            "fileorganizer-gui=main:main",
        ]
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json"],
    },
)