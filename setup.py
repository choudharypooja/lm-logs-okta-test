from setuptools import setup, find_packages
import configparser

NAME = "oktalogcollector"
config = configparser.ConfigParser()
with open("verson.properties") as fp:
    config.read_string("[" + NAME + "]\n" + fp.read())
    

setup(
    name=NAME,
    version=config[NAME].get('__version__'),
    packages=find_packages(),
    package_data={'': ['version.properties']},
    include_package_data=True,
    author="LogicMonitor",
    author_email="support@logicmonitor.com",
)
