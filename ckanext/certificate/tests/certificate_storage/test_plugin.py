import json
import requests
import ckan.plugins
from ckan import tests
from pylons import config
from ckan.new_tests import helpers, factories
from ckan import model
from nose.tools import assert_equal, assert_true, assert_false, assert_in
from logging import getLogger
from ckanext.certificate.tests.certificate_helpers import get_ckan_app

log = getLogger(__name__)


class TestAPIBase(object):

    @classmethod
    def setup_class(cls):
        cls.app = get_ckan_app(plugins=['certificate_storage'])

    def setup(self):
        # Delete any stuff that's been created in the db, so it doesn't
        # interfere with the next test.
        helpers.reset_db()
        # create a test dataset so that database is not empty
        factories.Dataset(name='test-dataset')


class TestPermissions(TestAPIBase):

    def test_unauthorised(self):
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'certificate': 'test-certificate'}),
                      headers={'content-type': 'application/json'},
                      status=403)

    def test_authorised(self):
        sysadmin = factories.Sysadmin()
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'certificate': 'test-certificate'}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=200)


class TestCertificateAssign(TestAPIBase):

    def test_missing_dataset(self):
        sysadmin = factories.Sysadmin()
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'missing-dataset', 'certificate': 'test-certificate'}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=404)

    def test_insufficient_params(self):
        sysadmin = factories.Sysadmin()
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'something': False}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=409)

    def test_new_certificate_is_assigned(self):
        sysadmin = factories.Sysadmin()
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'certificate': 'test-certificate'}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=200)
        updated_dataset = helpers.call_action('package_show', id='test-dataset')
        certificate = next(item['value'] for item in updated_dataset['extras'] if item['key'] == 'certificate')
        certificate = json.loads(certificate)
        assert_equal(certificate, 'test-certificate')

    def test_existing_certificate_is_updated(self):
        sysadmin = factories.Sysadmin()
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'certificate': 'test-certificate'}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=200)
        self.app.post('/api/3/action/certificate_assign',
                      params=json.dumps({'id': 'test-dataset', 'certificate': 'test-updated-certificate'}),
                      headers={'content-type': 'application/json', 'Authorization': str(sysadmin.get('apikey'))},
                      status=200)
        updated_dataset = helpers.call_action('package_show', id='test-dataset')
        certificate = next(item['value'] for item in updated_dataset['extras'] if item['key'] == 'certificate')
        certificate = json.loads(certificate)
        assert_equal(certificate, 'test-updated-certificate')
