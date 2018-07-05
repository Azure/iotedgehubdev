"""
My Tool does one thing, and one thing well.
"""
from setuptools import find_packages, setup

VERSION = '0.1.0'
# If we have source, validate that our version numbers match
# This should prevent uploading releases with mismatched versions.
try:
    with open('iotedgehubdev/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
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

dependencies = [
    'click',
    'docker',
    'pyOpenSSL',
    'requests',
    'six',
    'applicationinsights',
    'pyyaml',
    'jsonpath_rw'
]

setup(
    name='iotedgehubdev',
    version=VERSION,
    url='https://github.com/adashen/iotedgelocal',
    license='BSD',
    author='iotedgehubdev',
    author_email='shenwe@microsoft.com',
    description='My Tool does one thing, and one thing well.',
    long_description=__doc__,
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
        'License :: OSI Approved :: BSD License',
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
