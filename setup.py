import sys

from setuptools import setup

assert sys.version_info >= (3, 6, 0), "baw_client_rest requires Python 3.6+"

setup(
    name="baw_client_rest",
    description="A client to connect to the rest endpoints of BAW (Business Automation Workflow)",
    url="https://github.com/ONSdigital/baw-client-rest",
    license="MIT",
    packages=["baw_client_rest"],
    package_dir={"": "."},
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.1",
        "boto3>=1.17.9",
    ],
    test_suite="tests",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)