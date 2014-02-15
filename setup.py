import os, sys
from setuptools import setup, find_packages

requires = [
    'pyramid>=1.3dev',
]

if sys.version_info[:2] < (2, 7):
    requires.append('ordereddict')

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

setup(
    name='pyramid_assetmutator',
    version='0.1',
    author='Seth Davis',
    author_email='seth@curiasolutions.com',
    description="Dynamic asset mutation for Pyramid. Easily adds support " + \
                "for popular asset metalanguages such as CoffeeScript, " + \
                "SASS, SCSS, LESS, Dart, TypeScript, etc.",
    long_description=README + '\n\n' + CHANGES,
    url='http://github.com/seedifferently/pyramid_assetmutator',
    keywords='pyramid assets coffeescript sass scss less dart typescript css3',
    packages=find_packages(),
    install_requires=requires,
    tests_require=requires,
    license = "MIT",
    platforms = "Posix; MacOS X; Windows",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
    ]
)
