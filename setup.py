"""
Azure IoT EdgeHub Dev Tool
"""
from setuptools import find_packages, setup

VERSION = '0.14.14'
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('iotedgehubdev/__init__.py', 'rb') as f:
        content = f.read().decode('utf-8')
except OSError:
    pass
else:
    import re
    import sys
    m = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', content)
    if not m:
        print('Could not find __version__ in iotedgehubdev/__init__.py')
        sys.exit(1)
    if m.group(1) != VERSION:
        print('Expected __version__ = "{}"; found "{}"'.format(VERSION, m.group(1)))
        sys.exit(1)

with open('README.md', 'rb') as f:
    readme = f.read().decode('utf-8')

dependencies = [
    'click',
    'docker==5.0.3',
    'pyOpenSSL>=20.0.1',
    'requests>=2.25.1',
    'applicationinsights==0.11.9',
    'pyyaml>=5.4',
    'jsonpath_rw',
    'docker-compose==1.29.1',
    'regex'
]

setup(
    name='iotedgehubdev',
    version=VERSION,
    url='https://github.com/Azure/iotedgehubdev',
    license='MIT',
    author='iotedgehubdev',
    author_email='vsciet@microsoft.com',
    description='Azure IoT EdgeHub Dev Tool',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'iotedgehubdev = iotedgehubdev.cli:main',
        ],
    },
    python_requires='>=3.5, <3.10',
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
