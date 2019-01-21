"""
Azure IoT EdgeHub Dev Tool
"""
from setuptools import find_packages, setup

VERSION = '0.7.0rc0'
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
    'docker',
    'pyOpenSSL>=17.0.0',
    'requests',
    'six',
    'applicationinsights',
    'pyyaml',
    'jsonpath_rw'
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
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
