import json
import mock
import requests
import ckanext.certificate.auto_certification.tasks as tasks
import ckan.model as model
from ckan.new_tests import helpers, factories
from nose.tools import assert_equal, assert_true, assert_false, assert_in


# TODO: test that `certificate_assign` endpoint is called correctly after fetch is successful

class TestAPIBase(object):
    def setup(self):
        self.post_patcher = mock.patch('requests.post')
        self.post = self.post_patcher.start()

        self.get_patcher = mock.patch('requests.get')
        self.get = self.get_patcher.start()

        self.context = {
            'site_url': 'http://ckan.org',
            'certs_config': {
                'server': 'http://certificates.org',
                'username': 'test@test.com',
                'token': 'test-token'
            }
        }

        self.package = {
            'id': 'test',
            'url': 'http://ckan.org/dataset/test'
        }

    def teardown(self):
        self.post_patcher.stop()
        self.get_patcher.stop()


class TestCreateCertificate(TestAPIBase):
    def test_post_is_made(self):
        tasks.new.apply(args=[self.context, self.package])
        assert_true(self.post.called)

    def test_url(self):
        tasks.new.apply(args=[self.context, self.package])
        args, kwargs = self.post.call_args
        url = args[0]
        assert_equal(url, 'http://certificates.org/datasets')

    def test_content_type(self):
        tasks.new.apply(args=[self.context, self.package])
        args, kwargs = self.post.call_args
        content_type = kwargs['headers']['content-type']
        assert_equal('application/json', content_type)

    def test_auth(self):
        tasks.new.apply(args=[self.context, self.package])
        args, kwargs = self.post.call_args
        auth = kwargs['auth']
        assert_equal('test@test.com', auth[0])
        assert_equal('test-token', auth[1])

    def test_data(self):
        tasks.new.apply(args=[self.context, self.package])
        args, kwargs = self.post.call_args
        data = json.loads(kwargs['data'])
        assert_equal('GB', data['jurisdiction'])
        assert_equal('http://ckan.org/dataset/test',
                     data['dataset']['documentationUrl'])

    def test_fetch(self):
        self.post().json.return_value = {"success": "pending",
                                         "dataset_url": "http://certificates.org/datasets/status/1"}

        self.get.side_effect = [
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": "pending",
                                                   "dataset_url": "http://certificates.org/datasets/status/1"})),
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": True,
                                                   "dataset_url": "http://certificates.org/datasets/1.json",
                                                   "certificate_url": "http://certificates.org/datasets/1/certificate.json"})),
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={
                          "certificate": {
                              "level": "FooLevel",
                              "created_at": "FooCreated",
                              "jurisdiction": "FooJurisdiction",
                              "dataset": {
                                  "title": "FooTitle"
                              }
                          }
                      })),
        ]

        status_json = {'success': 'pending', 'dataset_url': 'http://certificates.org/datasets/status/1'}
        tasks.fetch.apply(args=[self.context, self.package, status_json])
        assert_equal(3, self.get.call_count)
