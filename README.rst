================================================================================
Pyramid AssetMutator v0.3
================================================================================

.. image:: https://travis-ci.org/seedifferently/pyramid_assetmutator.svg?branch=master
  :target: https://travis-ci.org/seedifferently/pyramid_assetmutator

| Copyright: (c) 2014 Seth Davis
| http://github.com/seedifferently/pyramid_assetmutator


Synopsis
================================================================================

Pyramid AssetMutator provides simple and dynamic asset mutation (also known as
compiling or piping) for your Pyramid_ applications.

Inspired by other more powerful asset management packages, its goal is to
provide a basic and straightforward mechanism for asset *compilation* (e.g.
CoffeeScript/LESS), *minification* (e.g. jsmin), and *optimization* (e.g.
pngcrush).

As of version 0.3, it also adds experimental support for template language
parsing (e.g. you could use view helpers like `request.route_url()` in your
CoffeeScript by installing the `pyramid_jinja2` package and using
application.coffee.jinja2 as the asset source filename).

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

You can read the documentation at: http://pyramid_assetmutator.readthedocs.org/


Known Issues and Limitations
================================================================================

* Experimental support for Py3k/pypy.
* Doesn't clean up after itself (compiled/mutated assets aren't removed
  automatically).
* Mutator "commands" must print to stdout (see the documentation for more info).
* Hopefully obvious, but you have to actually have the specified compiler
  command installed and accessible from your working path in order for it to
  work.


Disclaimers and Warnings
================================================================================

This is Alpha software--use at your own risk!

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHOR BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
