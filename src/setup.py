from setuptools import setup, find_packages

setup(
    name="tableau-migration-tool",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'tableauserverclient>=0.17.0',
        'python-dotenv>=0.19.0',
        'tqdm>=4.65.0',
        'prometheus_client>=0.17.0',
    ],
    author="BigX Data",
    author_email="support@bigxdata.co.kr",
    description="Tableau Server to Cloud Data Source Migration Tool",
    long_description=open('docs/README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bigxdata/tableau-migration-tool",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)