import os, sys
from setuptools import setup, find_packages

# Package requirements
install_requires = [
    'pyramid >= 1.3',
]
# If less than Python v2.7, we'll also need the `ordereddict` package
if sys.version_info[:2] < (2, 7):
    install_requires.append('ordereddict')

# Package requirements for testing
tests_require = install_requires[:]
tests_require.extend(['nose', 'coverage', 'webtest', 'pyramid_chameleon',
                      'pyramid_jinja2'])

# Prepare README and CHANGES description info
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

setup(
    name='pyramid_assetmutator',
    version='1.0b1',
    author='Seth Davis',
    author_email='seth@curiasolutions.com',
    description='Dynamic asset mutation for Pyramid. Easily adds support ' + \
                'for popular asset metalanguages such as CoffeeScript, ' + \
                'SASS, SCSS, LESS, Dart, TypeScript, etc.',
    long_description=README + '\n\n' + CHANGES,
    url='http://pyramid-assetmutator.curia.solutions/',
    keywords='pyramid assets coffeescript sass scss less dart typescript css3',
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='pyramid_assetmutator',
    license = 'MIT',
    platforms = 'Posix; MacOS X; Windows',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
