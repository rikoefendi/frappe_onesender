from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in frappe_whatsapp/__init__.py
from frappe_onesender import __version__ as version

setup(
    name="frappe_onesender",
    version=version,
    description="OneSender integration for frappe",
    author="Madina Kebab",
    author_email="web.madinakebab@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
