#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


def read_requirements(file):
    with open(file) as f:
        return f.read().splitlines()


requirements = read_requirements('requirements.txt')
test_requirements = read_requirements('requirements.txt')

setup(
    author="Vapi AI",
    author_email='team@vapi.ai',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="This package lets you start Vapi calls directly from Python.",
    entry_points={
        'console_scripts': [
            'vapi_python=vapi_python.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='vapi_python',
    name='vapi_python',
    packages=find_packages(include=['vapi_python', 'vapi_python.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/jordan.cde/vapi_python',
    version='0.1.5',
    zip_safe=False,
)
