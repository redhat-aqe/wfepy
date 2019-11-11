from setuptools import setup
from os import path
import re


version = None
with open(path.join('wfepy', '__init__.py')) as f:
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
    name='wfepy',
    version=version,
    description='Workflow Engine for Python',
    long_description=long_description,
    author='Filip Poboril',
    author_email='fpoboril@redhat.com',
    url='https://github.com/redhat-aqe/wfepy',
    download_url='https://github.com/redhat-aqe/wfepy/archive/v{v}.tar.gz'.format(v=version),
    license='MIT',
    keywords=['Workflow', 'Workflow Engine'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    packages=['wfepy'],
    install_requires=['attrs', 'graphviz'],
)
