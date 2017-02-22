================================================================================
Pyramid AssetMutator v1.0b1
================================================================================

.. image:: https://travis-ci.org/seedifferently/pyramid_assetmutator.svg?branch=master
  :target: https://travis-ci.org/seedifferently/pyramid_assetmutator

| Copyright: (c) 2017 Seth Davis
| http://pyramid-assetmutator.curia.solutions/


Synopsis
================================================================================

Pyramid AssetMutator provides simple and flexible asset mutation (also known as
compiling or piping) for your Pyramid_ applications.

Inspired by other more powerful asset management packages, its goal is to
provide Pyramid developers with a basic and straightforward mechanism for
utilizing asset *compilation* (e.g. for CoffeeScript/Sass), *minification*
(e.g. with jsmin), and *optimization* (e.g. with pngcrush).

As of version 0.3, it also adds experimental support for template language
parsing (e.g. you could use Pyramid helpers like ``request.route_url()`` within
your CoffeeScript files by using ``application.coffee.pt`` as the asset source
filename).

.. _Pyramid: http://www.pylonsproject.org/


Installation
================================================================================

To install, simply::

    pip install pyramid_assetmutator

* You'll need to have `Python`_ 2.6+ and `pip`_ installed.

.. _Python: http://www.python.org
.. _pip: http://www.pip-installer.org


Documentation
================================================================================

You can read the documentation at: http://pyramid-assetmutator.curia.solutions/


Known Issues and Limitations
================================================================================

* Experimental support for pypy.
* Doesn't clean up after itself by default (e.g. mutated assets aren't removed
  automatically when the default settings are used).
* Mutator "commands" must print to stdout (see the documentation for more info).
* Hopefully obvious, but you must actually have the specified source compiler
  command installed and accessible from your working path in order for it to
  function.


Disclaimers and Warnings
================================================================================

This is Beta software--use at your own risk!

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHOR BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
