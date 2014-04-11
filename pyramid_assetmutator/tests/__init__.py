# vim:fileencoding=utf-8:ai:ts=4:sts:et:sw=4:tw=80:
import sys
import os
import hashlib
import unittest
from webtest import TestApp
from pyramid import testing

from pyramid_assetmutator.compat import *
from pyramid_assetmutator.mutator import Mutator

class TestParseSettings(unittest.TestCase):
    def _callFUT(self, settings):
        from pyramid_assetmutator import parse_settings
        return parse_settings(settings)

    def test_it(self):
        settings = {
            'assetmutator.debug':'true',
            'assetmutator.remutate_check':'checksum',
            'assetmutator.asset_prefix':'.',
            'assetmutator.mutated_path': 'pyramid_assetmutator:static/cache/',
            'assetmutator.each_request': 'false',
            'assetmutator.each_boot': 'true',
            'assetmutator.asset_paths': 'pyramid_assetmutator:static/css/\n' + \
                                        'pyramid_assetmutator:static/js/'
        }
        result = self._callFUT(settings)
        self.assertEqual(
            result,
            {'assetmutator.debug': True,
             'assetmutator.remutate_check':'checksum',
             'assetmutator.asset_prefix':'.',
             'assetmutator.mutated_path': 'pyramid_assetmutator:static/cache/',
             'assetmutator.each_request': False,
             'assetmutator.each_boot': True,
             'assetmutator.asset_paths': ['pyramid_assetmutator:static/css/',
                                          'pyramid_assetmutator:static/js/']}
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
        self.assertEqual(settings['assetmutator.remutate_check'], 'mtime')
        self.assertEqual(settings['assetmutator.asset_prefix'], '_')
        self.assertEqual(settings['assetmutator.mutated_path'], '')
        self.assertEqual(settings['assetmutator.each_request'], True)
        self.assertEqual(settings['assetmutator.each_boot'], False)
        self.assertEqual(settings['assetmutator.asset_paths'], [])

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

        self.assertRaises(ValueError, Mutator, self.request,
                          'pyramid_assetmutator.tests:fixtures/test.json')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(ValueError) as exc:
                Mutator(self.request,
                        'pyramid_assetmutator.tests:fixtures/test.json')
            self.assertEqual('%s' % exc.exception, 'No mutators were found.')

    def test_mutator_not_found(self):
        self.assertRaises(ValueError, Mutator, self.request,
                          'pyramid_assetmutator.tests:fixtures/test.json',
                          mutator='spam')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(ValueError) as exc:
                Mutator(self.request,
                        'pyramid_assetmutator.tests:fixtures/test.json',
                        mutator='spam')
            self.assertEqual('%s' % exc.exception, 'No mutator found for json.')

    def test_mutator_source_not_found(self):
        self.settings['assetmutator.remutate_check'] = 'exists'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')

        self.assertRaises(ValueError, mutant.mutated_data)

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(ValueError) as exc:
                mutant.mutated_data()
            self.assertEqual('%s' % exc.exception,
                             'Source not found. Has it been mutated?')

    def test_mutator_source_mtime(self):
        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        mtime = os.path.getmtime('%s/fixtures/test.json' % self.here)
        filename = '%s/fixtures/_test.%s.txt' % (self.here, mtime)
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_exists(self):
        self.settings['assetmutator.remutate_check'] = 'exists'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')

        if not mutant.mutated:
            mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/_test.txt' % self.here
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(mutant._check_exists(filename))

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

        checksum = compute_checksum('%s/fixtures/test.json' % self.here)
        filename = '%s/fixtures/_test.%s.txt' % (self.here, checksum)
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_specified_mutator(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json',
                         mutator='json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/_test.txt' % self.here
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_mutated_path(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.mutated_path'] = \
            'pyramid_assetmutator.tests:cache'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        dirname = '%s/cache' % self.here
        filename = '%s/_test.txt' % dirname
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_source_asset_prefix(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        self.settings['assetmutator.asset_prefix'] = '~'

        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json')
        mutant.mutate()

        self.assertEqual(
            mutant.mutated_data(),
            '{"spam": "lorem", "eggs": "鸡蛋"}\n'
        )

        filename = '%s/fixtures/~test.txt' % self.here
        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_mutator_binary_mutator(self):
        self.settings['assetmutator.remutate_check'] = 'exists'
        mutant = Mutator(self.request,
                         'pyramid_assetmutator.tests:fixtures/test.json',
                         mutator=dict(cmd='gzip --stdout', ext='json.gz'))
        mutant.mutate()

        filename = '%s/fixtures/_test.json.gz' % self.here
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
        source = '%s/fixtures/test.json' % self.here
        filename = '%s/fixtures/_test.txt' % self.here

        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))

        os.remove(filename)

        testing.tearDown()

    def test_assetmutator_url(self):
        template = '%s/fixtures/test_assetmutator_url.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), 'http://localhost/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

    def test_assetmutator_path(self):
        template = '%s/fixtures/test_assetmutator_path.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), '/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

    def test_assetmutator_source(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

        template = '%s/fixtures/test_assetmutator_source.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        resp.mustcontain('{"spam": "lorem", "eggs": "鸡蛋"}')

    def test_assetmutator_assetpath(self):
        template = '%s/fixtures/test_assetmutator_assetpath.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(),
                         'pyramid_assetmutator.tests:fixtures/_test.txt')

    def test_each_boot(self):
        self.config.registry.settings['assetmutator.each_request'] = 'false'
        self.config.registry.settings['assetmutator.each_boot'] = 'true'
        self.config.registry.settings['assetmutator.asset_paths'] = \
            ['pyramid_assetmutator.tests:fixtures',
             'pyramid_assetmutator.tests:fixtures/subdir']
        self.app = TestApp(self.config.make_wsgi_app())

        source2 = '%s/fixtures/subdir/test2.json' % self.here
        filename2 = '%s/fixtures/subdir/_test2.txt' % self.here
        self.assertTrue(os.path.exists(filename2))
        self.assertEqual(os.path.getsize(filename2), os.path.getsize(source2))
        os.remove(filename2)

class TestPyramidRenderedMutator(unittest.TestCase):
    def setUp(self):
        self.here = os.path.abspath(os.path.dirname(__file__))
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
        filename = '%s/cache/_test.txt' % self.here

        self.assertTrue(os.path.exists(source))
        self.assertTrue(os.path.exists(filename))
        self.assertEqual(os.path.getsize(filename), os.path.getsize(source))
        self.assertTrue(os.path.getsize(filename) > 30)

        os.remove(source)
        os.remove(filename)

        testing.tearDown()

    def test_assetmutator_url_rendered_pt(self):
        template = '%s/fixtures/test_assetmutator_url_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), 'http://localhost/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_path_rendered_pt(self):
        template = '%s/fixtures/test_assetmutator_path_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), '/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"request_url": "http://localhost/?one=1"}')

    def test_assetmutator_source_rendered_pt(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

        template = ('%s/fixtures/test_assetmutator_source_rendered.pt' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_url_rendered_jinja2(self):
        template = ('%s/fixtures/test_assetmutator_url_rendered.jinja2' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), 'http://localhost/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"request_url": "http://localhost/?one=1"}')

    def test_assetmutator_path_rendered_jinja2(self):
        template = ('%s/fixtures/test_assetmutator_path_rendered.jinja2' %
                    self.here)
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')
        self.assertEqual(resp.text.strip(), '/static/_test.txt')
        resp = self.app.get(resp.text.strip())
        resp.mustcontain('{"spam": "spam", "eggs": "鸡蛋"}')

    def test_assetmutator_source_rendered_jinja2(self):
        if not PY3:
            reload(sys)
            sys.setdefaultencoding('utf-8')

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

        checksum = compute_checksum('%s/fixtures/test.json.pt' % self.here)
        rendered_filename = '%s/cache/_test.json' % (self.here)
        checksum_filename = '%s/cache/_test.%s.txt' % (self.here,
                                                                checksum)
        self.assertTrue(os.path.exists(rendered_filename))
        self.assertTrue(os.path.exists(checksum_filename))

        os.remove(rendered_filename)

        resp = self.app.get('/')

        self.assertFalse(os.path.exists(rendered_filename))
        os.remove(checksum_filename)

        self.config.registry.settings['assetmutator.remutate_check'] = 'exists'

        resp = self.app.get('/')

    def test_assetmutator_url_rendered_pt_no_mutated_path(self):
        template = '%s/fixtures/test_assetmutator_url_rendered.pt' % self.here
        self.config.add_view(route_name='home', view=home, renderer=template)
        self.app = TestApp(self.config.make_wsgi_app())
        resp = self.app.get('/')

        self.config.registry.settings['assetmutator.mutated_path'] = ''

        self.assertRaises(ValueError, self.app.get, '/')

        if sys.version_info[:2] > (2, 6):
            with self.assertRaises(ValueError) as exc:
                self.app.get('/')
            self.assertTrue(
                str(exc.exception).startswith('No mutator found for pt.')
            )

def compute_checksum(path):
    md5 = hashlib.md5()

    # Loop the file, adding chunks to the MD5 generator
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)
    # Finally, add the mtime
    md5.update(str(os.path.getmtime(path)).encode('utf-8'))

    # Return the first 12 characters of the hexdigest
    return md5.hexdigest()[:12]

def home(request):
    return {'spam': 'spam', 'eggs': '鸡蛋'}
