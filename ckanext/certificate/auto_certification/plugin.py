import ckan.plugins as p
from urlparse import urljoin
from logging import getLogger
from ckan import model
from ckan.plugins import toolkit
from ckan.lib.celery_app import celery
from ckan.model.types import make_uuid

log = getLogger(__name__)


def _extract_certificate(data_dict):
    '''
    Extracts the value of the 'certificate' key stored in extras field of the dataset.
    '''
    try:
        certificate = _extract_value_from_extras(data_dict['extras'], 'certificate')
        return json.loads(certificate)
    except:
        return None

def _extract_value_from_extras(extras, key):
    '''
    Extracts the value of a given key in extras.

    ...because extras are stored as an array of dictionaries:
    [{'key': 'the-key', 'value': 'the-value'}]
    '''
    return next((x['value'] for x in extras if x['key'] == key), None)

class AutoCertification(p.SingletonPlugin):
    '''
    The plugin that sends requests to
    '''

    p.implements(p.IConfigurable)
    p.implements(p.IPackageController, inherit=True)

    # IConfigurable

    def configure(self, config):
        self.site_url = config.get('ckan.site_url')
        self.certs_config = {
            'server': config.get('ckanext.certificate.server'),
            'username': config.get('ckanext.certificate.username'),
            'token': config.get('ckanext.certificate.token')
        }

    # IPackageController

    def after_create(self, context, data):
        if self._has_certs_config():
            log.debug("Scheduling new certificate task for new '%s' dataset", data['name'])
            celery.send_task(
                'certificate.new',
                args=[self._get_task_context(context), self._get_package_data(data), True],
                task_id=make_uuid()
            )

    def after_update(self, context, data):
        if self._has_certs_config():
            log.debug("Scheduling new certificate task for existing '%s' dataset", data['name'])
            celery.send_task(
                'certificate.new',
                args=[self._get_task_context(context), self._get_package_data(data), True],
                task_id=make_uuid()
            )

    # Private

    def _has_certs_config(self):
        '''
        Checks if all certificates configuration fields are specified.
        '''
        return all([self.certs_config[key] for key in ['server', 'username', 'token']])

    def _get_task_context(self, context):
        '''
        Returns the `context` parameter that is passed onto the background tasks.
        '''
        # BUG: gets 'odi' user, which is a deleted sysadmin.
        # Should instead get 'daniel', the current sysadmin.
        sysadmin = p.toolkit.get_action('get_site_user')(context)

        return {
            'site_url': self.site_url,
            'certs_config': self.certs_config,
            'apikey': sysadmin.get('apikey')
        }

    def _get_package_data(self, data):
        '''
        Returns the `package` parameter that is passed onto the background tasks.
        '''
        return {
            'id': data['name'],
            'url': self._get_package_url(data),
            'certificate': _extract_certificate(data)
        }

    def _get_package_url(self, data):
        '''
        Returns the full URL (HTML page) of the package.
        '''
        return urljoin(
            self.site_url,
            toolkit.url_for(
                controller='package',
                action='read',
                id=data['name']
            )
        )
