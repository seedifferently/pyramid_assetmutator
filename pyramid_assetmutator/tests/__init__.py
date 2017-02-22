# -*- coding: utf-8 -*-
import sys
import os
import time
import hashlib
import unittest
from webtest import TestApp
from pyramid import testing

from pyramid_assetmutator.compat import *
from pyramid_assetmutator.utils import *
from pyramid_assetmutator.mutator import Mutator

class TestParseSettings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_assetmutator import parse_settings
        return parse_settings(settings)

    def test_it(self):
        settings = {
            'assetmutator.debug':'true',
            'assetmutator.remutate_check':'checksum',
            'assetmutator.each_request': 'false',
            'assetmutator.each_boot': 'pyramid_assetmutator:static/*.css\n' + \
                                      'pyramid_assetmutator:static/*.js',
            'assetmutator.mutated_file_prefix':'.',
            'assetmutator.mutated_path': 'pyramid_assetmutator:static/cache/',
            'assetmutator.always_remutate': '*'

        }
        result = self._callFUT(settings)
        self.assertEqual(
            result,
            {'assetmutator.debug': True,
             'assetmutator.remutate_check': 'checksum',
             'assetmutator.each_request': False,
             'assetmutator.each_boot': ['pyramid_assetmutator:static/*.css',
                                        'pyramid_assetmutator:static/*.js'],
             'assetmutator.mutated_file_prefix': '.',
             'assetmutator.mutated_path': 'pyramid_assetmutator:static/cache/',
             'assetmutator.purge_mutated_path': False,
             'assetmutator.always_remutate': ['*']}
        )

class TestIncludeme(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def _callFUT(self, config):
        from pyramid_assetmutator import includeme
        return includeme(config)

    def test_it(self):
        self._callFUT(self.config)
        settings = self.config.registry.settings
        self.assertEqual(settings['assetmutator.debug'], False)
        self.assertEqual(settings['assetmutator.remutate_check'], 'stat')
        self.assertEqual(settings['assetmutator.each_request'], True)
        self.assertEqual(settings['assetmutator.each_boot'], [])
        self.assertEqual(settings['assetmutator.mutated_file_prefix'], '_')
        self.assertEqual(settings['assetmutator.mutated_path'], '')

class TestMutator(unittest.TestCase):
    def setUp(self):
        from pyramid_assetmutator import mutators
        self.here = os.path.abspath(os.path.dirname(__file__))
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.settings = self.config.registry.settings
        self.config.include('pyramid_assetmutator')
        self.config.assign_assetmutator('json', 'cat', 'txt')
        self.settings['assetmutator.mutators'] = mutators
        self.fixture_path = os.path.join(self.here, 'fixtures', 'test.json')

    def tearDown(self):
        testing.tearDown()

    def test_mutator_none_found(self):
        self.settings['assetmutator.mutators'] = None

        self.assertRaises(RuntimeError, Mutator, self.request,
                          'pyramid_assetmutator.tests:fixtures/test.json')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(RuntimeError) as exc:
                Mutator(self.request,
                        'pyramid_assetmutator.tests:fixtures/test.json')
            self.assertEqual('%s' % exc.exception, 'No mutators were found.')

    def test_mutator_not_found(self):
        self.assertRaises(RuntimeError, Mutator, self.request,
                          'pyramid_assetmutator.tests:fixtures/test.json',
                          mutator='spam')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(RuntimeError) as exc:
                Mutator(self.request,
                        'pyramid_assetmutator.tests:fixtures/test.json',
                        mutator='spam')
            self.assertEqual('%s' % exc.exception, 'No mutator found for json.')

    def test_mutator_source_not_found(self):
        self.settings['assetmutator.remutate_check'] = 'exists'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')

        self.assertRaises(RuntimeError, mutant.mutated_data)

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(RuntimeError) as exc:
                mutant.mutated_data()
            self.assertEqual('%s' % exc.exception,
                             'Source not found. Has it been mutated?')

    def test_mutator_source_stat(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        size = str(os.path.getsize('%s/fixtures/test.json' % self.here))
        mtime = str(os.path.getmtime('%s/fixtures/test.json' % self.here))
        fingerprint = hexhashify(src_fullpath) + hexhashify(size + '.' + mtime)
        filename = '%s/fixtures/_test.%s.txt' % (self.here, fingerprint)
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_exists(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)

        if not mutant.is_mutated:
            mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_checksum(self):
        self.settings['assetmutator.remutate_check'] = 'checksum'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        checksum = compute_md5('%s/fixtures/test.json' % self.here)
        filename = '%s/fixtures/_test.%s.txt' % (self.here, checksum)
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_specified_mutator(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path, mutator='json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_mutated_path(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.mutated_path'] = \
            'pyramid_assetmutator.tests:cache'
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        dirname = '%s/cache' % self.here
        filename = '%s/_test.%s.txt' % (dirname, hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_mutated_file_prefix(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.mutated_file_prefix'] = '~'
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/~test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_mutated_always_remutate_all(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.mutated_path'] = \
            'pyramid_assetmutator.tests:cache'
        self.settings['assetmutator.always_remutate'] = ['*']
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        dirname = '%s/cache' % self.here
        filename = '%s/_test.%s.txt' % (dirname, hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        stat = get_stat(filename)

        # Pause, remutate, and verify file was changed
        time.sleep(0.1)
        mutant.mutate()
        self.assertNotEqual(stat, get_stat(filename))

        os.remove(filename)

    def test_mutator_mutated_always_remutate_json(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.mutated_path'] = \
            'pyramid_assetmutator.tests:cache'
        self.settings['assetmutator.always_remutate'] = ['*.json']
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path)
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        dirname = '%s/cache' % self.here
        filename = '%s/_test.%s.txt' % (dirname, hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        stat = get_stat(filename)

        # Pause, remutate, and verify file was changed
        time.sleep(0.1)
        mutant.mutate()
        self.assertNotEqual(stat, get_stat(filename))

        os.remove(filename)

    def test_mutator_binary_mutator(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        mutant = Mutator(self.request, path,
                         mutator=dict(cmd='gzip --stdout', ext='json.gz'))
        mutant.mutate()

        filename = '%s/fixtures/_test.%s.json.gz' % (self.here,
                                                     hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))

        import gzip
        f = gzip.open(filename)
        content = f.read()
        f.close()

        if PY3:
            content = content.decode('utf-8')

        self.assertEqual(
            content,
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        os.remove(filename)

class TestPyramidMutator(unittest.TestCase):
    def setUp(self):
        self.here = os.path.abspath(os.path.dirname(__file__))
        self.config = testing.setUp()
        self.config.include('pyramid_assetmutator')
        self.config.include('pyramid_chameleon')
        self.config.registry.settings['assetmutator.remutate_check'] = 'exists'
        self.config.add_static_view('static',
                                    'pyramid_assetmutator.tests:fixtures')
        self.config.add_route('home', '/')

    def tearDown(self):
        testing.tearDown()

    def test_assetmutator_url(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        template = '%s/fixtures/test_assetmutator_url.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(
            resp.text.strip(),
            'http://localhost/static/_test.%s.txt' % hexhashify(src_fullpath)
        )
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

    def test_assetmutator_path(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        template = '%s/fixtures/test_assetmutator_path.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(),
                         '/static/_test.%s.txt' % hexhashify(src_fullpath))
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

    def test_assetmutator_source(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        template = '%s/fixtures/test_assetmutator_source.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

    def test_assetmutator_assetpath(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json'
        src_fullpath = get_abspath(path)
        template = '%s/fixtures/test_assetmutator_assetpath.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(
            resp.text.strip(),
            'pyramid_assetmutator.tests:fixtures/_test.%s.txt' % \
                hexhashify(src_fullpath)
        )

        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(src_fullpath))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

    def test_each_boot_exists(self):
        self.config.registry.settings['assetmutator.each_request'] = 'false'
        self.config.registry.settings['assetmutator.each_boot'] = \
            ['pyramid_assetmutator.tests:fixtures/*.json',
             'pyramid_assetmutator.tests:fixtures/subdir/*.json']
        self.app = TestApp(self.config.make_wsgi_app())

        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.%s.txt' % (self.here,
                                                 hexhashify(source))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

        source2 = '%s/fixtures/subdir/test2.json' % self.here
        filename2 = '%s/fixtures/subdir/_test2.%s.txt' % (self.here,
                                                          hexhashify(source2))
        self.assertTrue(os.path.exists(filename2))
        self.assertEqual(os.path.getsize(filename2), os.path.getsize(source2))
        os.remove(filename2)

        source3 = '%s/fixtures/subdir/test3.json' % self.here
        filename3 = '%s/fixtures/subdir/_test3.%s.txt' % (self.here,
                                                          hexhashify(source3))
        self.assertTrue(os.path.exists(filename3))
        self.assertEqual(os.path.getsize(filename3), os.path.getsize(source3))
        os.remove(filename3)

    def test_each_boot_stat(self):
        self.config.registry.settings['assetmutator.each_request'] = 'false'
        self.config.registry.settings['assetmutator.remutate_check'] = 'stat'
        self.config.registry.settings['assetmutator.each_boot'] = \
            ['pyramid_assetmutator.tests:fixtures/*.json',
             'pyramid_assetmutator.tests:fixtures/subdir/*.json']
        self.app = TestApp(self.config.make_wsgi_app())

        source = '%s/fixtures/test.json' % self.here
        source2 = '%s/fixtures/subdir/test2.json' % self.here
        source3 = '%s/fixtures/subdir/test3.json' % self.here

        size = str(os.path.getsize('%s/fixtures/test.json' % self.here))
        size2 = str(os.path.getsize('%s/fixtures/subdir/test2.json' % self.here))
        size3 = str(os.path.getsize('%s/fixtures/subdir/test3.json' % self.here))

        mtime = str(os.path.getmtime('%s/fixtures/test.json' % self.here))
        mtime2 = str(os.path.getmtime('%s/fixtures/subdir/test2.json' % self.here))
        mtime3 = str(os.path.getmtime('%s/fixtures/subdir/test3.json' % self.here))

        fingerprint = hexhashify(source) + hexhashify(size + '.' + mtime)
        filename = '%s/fixtures/_test.%s.txt' % (self.here, fingerprint)
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

        fingerprint = hexhashify(source2) + hexhashify(size2 + '.' + mtime2)
        filename2 = '%s/fixtures/subdir/_test2.%s.txt' % (self.here, fingerprint)
        self.assertTrue(os.path.exists(filename2))
        self.assertEqual(os.path.getsize(filename2), os.path.getsize(source2))
        os.remove(filename2)

        fingerprint = hexhashify(source3) + hexhashify(size3 + '.' + mtime3)
        filename3 = '%s/fixtures/subdir/_test3.%s.txt' % (self.here, fingerprint)
        self.assertTrue(os.path.exists(filename3))
        self.assertEqual(os.path.getsize(filename3), os.path.getsize(source3))
        os.remove(filename3)

    def test_each_boot_checksum(self):
        self.config.registry.settings['assetmutator.remutate_check'] = \
            'checksum'
        self.config.registry.settings['assetmutator.each_request'] = 'false'
        self.config.registry.settings['assetmutator.each_boot'] = \
            ['pyramid_assetmutator.tests:fixtures/*.json',
             'pyramid_assetmutator.tests:fixtures/subdir/*.json']
        self.app = TestApp(self.config.make_wsgi_app())

        source = '%s/fixtures/test.json' % self.here
        source2 = '%s/fixtures/subdir/test2.json' % self.here
        source3 = '%s/fixtures/subdir/test3.json' % self.here

        checksum = compute_md5('%s/fixtures/test.json' % self.here)
        checksum2 = compute_md5('%s/fixtures/subdir/test2.json' % self.here)
        checksum3 = compute_md5('%s/fixtures/subdir/test3.json' % self.here)

        filename = '%s/fixtures/_test.%s.txt' % (self.here, checksum)
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        os.remove(filename)

        filename2 = '%s/fixtures/subdir/_test2.%s.txt' % (self.here, checksum2)
        self.assertTrue(os.path.exists(filename2))
        self.assertEqual(os.path.getsize(filename2), os.path.getsize(source2))
        os.remove(filename2)

        filename3 = '%s/fixtures/subdir/_test3.%s.txt' % (self.here, checksum3)
        self.assertTrue(os.path.exists(filename3))
        self.assertEqual(os.path.getsize(filename3), os.path.getsize(source3))
        os.remove(filename3)

class TestPyramidRenderedMutator(unittest.TestCase):
    def setUp(self):
        self.here = os.path.abspath(os.path.dirname(__file__))
        self.fingerprint = None
        self.config = testing.setUp()
        self.config.include('pyramid_assetmutator')
        self.config.include('pyramid_chameleon')
        self.config.include('pyramid_jinja2')
        self.config.registry.settings['assetmutator.remutate_check'] = 'exists'
        self.config.registry.settings['assetmutator.mutated_path'] = \
            'pyramid_assetmutator.tests:cache'
        self.config.add_static_view('static',
                                    'pyramid_assetmutator.tests:fixtures')
        self.config.add_static_view('static',
                                    'pyramid_assetmutator.tests:cache')
        self.config.add_route('home', '/')

    def tearDown(self):
        source = '%s/cache/_test.json' % self.here
        filename = '%s/cache/_test.%s.txt' % (self.here, self.fingerprint)

        self.assertTrue(os.path.exists(source))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        self.assertTrue(os.path.getsize(filename) > 30)

        os.remove(source)
        os.remove(filename)

        testing.tearDown()

    def test_assetmutator_url_rendered_pt(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json.pt'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = '%s/fixtures/test_assetmutator_url_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(
            resp.text.strip(),
            'http://localhost/static/_test.%s.txt' % self.fingerprint
        )
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_path_rendered_pt(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json.jinja2'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = '%s/fixtures/test_assetmutator_path_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(),
                         '/static/_test.%s.txt' % self.fingerprint)
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"request_url": "http://localhost/?one=1"}')

    def test_assetmutator_source_rendered_pt(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

        path = 'pyramid_assetmutator.tests:fixtures/test.json.pt'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = ('%s/fixtures/test_assetmutator_source_rendered.pt' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_url_rendered_jinja2(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json.jinja2'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = ('%s/fixtures/test_assetmutator_url_rendered.jinja2' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(
            resp.text.strip(),
            'http://localhost/static/_test.%s.txt' % self.fingerprint
        )
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"request_url": "http://localhost/?one=1"}')

    def test_assetmutator_path_rendered_jinja2(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json.pt'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = ('%s/fixtures/test_assetmutator_path_rendered.jinja2' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(),
                         '/static/_test.%s.txt' % self.fingerprint)
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_source_rendered_jinja2(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

        path = 'pyramid_assetmutator.tests:fixtures/test.json.jinja2'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = ('%s/fixtures/test_assetmutator_source_rendered.jinja2' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        resp.mustcontain('{"request_url": "http://localhost/?one=1"}')

    def test_assetmutator_url_rendered_pt_checksum_shouldnt_recreate(self):
        template = '%s/fixtures/test_assetmutator_url_rendered.pt' % self.here
        self.config.registry.settings['assetmutator.remutate_check'] = \
            'checksum'
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')

        checksum = compute_md5('%s/fixtures/test.json.pt' % self.here)
        rendered_filename = '%s/cache/_test.json' % (self.here)
        checksum_filename = '%s/cache/_test.%s.txt' % (self.here, checksum)
        self.assertTrue(os.path.exists(rendered_filename))
        self.assertTrue(os.path.exists(checksum_filename))

        os.remove(rendered_filename)

        resp = self.app.get('/')

        self.assertFalse(os.path.exists(rendered_filename))
        os.remove(checksum_filename)

        self.config.registry.settings['assetmutator.remutate_check'] = 'exists'
        path = 'pyramid_assetmutator.tests:fixtures/test.json.pt'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)

        resp = self.app.get('/')

    def test_assetmutator_url_rendered_pt_no_mutated_path(self):
        path = 'pyramid_assetmutator.tests:fixtures/test.json.pt'
        src_fullpath = get_abspath(path)
        self.fingerprint = hexhashify(src_fullpath)
        template = '%s/fixtures/test_assetmutator_url_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')

        self.config.registry.settings['assetmutator.mutated_path'] = ''

        self.assertRaises(RuntimeError, self.app.get, '/')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(RuntimeError) as exc:
                self.app.get('/')
            self.assertTrue(
                str(exc.exception).startswith('No mutator found for pt.')
            )

def home(request):
    return {'spam': 'spam', 'eggs': '鸡蛋'}
