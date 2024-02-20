"""Setup.py for the Kinetica Airflow provider package."""

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

__version__ = "1.0.1"

"""Perform the package airflow-provider-kinetica setup."""
setup(
    name="airflow-provider-kinetica",
    description="Kinetica provider package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chad Juliano",
    author_email="cjuliano@kinetica.com",
    url="https://kinetica.com/",
    version=__version__,
    license="Apache License 2.0",
    license_files = ["LICENSE"],
    classifiers=[
        "Framework :: Apache Airflow",
        "Framework :: Apache Airflow :: Provider",
    ],

    python_requires="~=3.8",
    packages=find_packages(exclude=["*tests.*", "*tests"]),
    setup_requires=[
        "setuptools", 
        "wheel"],
    install_requires=[
        "apache-airflow>=2.3", 
        "gpudb", 
        "apache-airflow-providers-apache-spark"],

    entry_points={
        "apache_airflow_provider": ["provider_info=kinetica_provider.get_provider_info:get_provider_info"]
    }
)
