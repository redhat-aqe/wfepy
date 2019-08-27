from setuptools import setup
from os import path
import re


version = None
with open(path.join('wfpy', '__init__.py')) as f:
    version_cre = re.compile(
        r'^__version__\s+=\s+[\'"](?P<version>\d+\.\d+.*)[\'"]$'
    )
    for line in f:
        match = version_cre.match(line)
        if match:
            version = match.group('version')
            break

with open('README.rst') as f:
    long_description = f.read()


setup(
    name='wfpy',
    version=version,
    description='',
    long_description=long_description,
    author='Filip Pobořil',
    author_email='tsuki@fpob.cz',
    url='https://gitlab.com/fpob/wfpy',
    download_url='https://gitlab.com/fpob/wfpy/-/archive/v{v}/wfpy-v{v}.zip'.format(v=version),
    license='MIT',
    keywords=['Workflow'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    packages=['wfpy'],
    install_requires=['attrs'],
)
