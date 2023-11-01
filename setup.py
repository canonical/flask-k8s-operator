import os.path
import pathlib

from setuptools import setup

requirements = ["cosl", "jsonschema>=4.19,<4.20", "ops", "pydantic>=1.10,<2"]

setup(
    name="xiilib",
    version="0.1.0",
    description="Companion library for 12-factor charms",
    url="https://github.com/canonical/flask-k8s-operator",
    author="IS DevOps team",
    author_email="is-devops-team@canonical.com",
    packages=["xiilib", "xiilib.flask"],
    package_dir={"xiilib": "./lib/xiilib", "xiilib.flask": "./lib/xiilib/flask"},
    install_requires=requirements,
    package_data={"xiilib.flask": ["cos/**"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
