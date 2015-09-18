import os
import json
import requests
from urlparse import urljoin
from ckan.lib.celery_app import celery
from ckan.model.types import make_uuid
from logging import getLogger

log = getLogger(__name__)


def _certificate_request_data(package_url):
    '''
    Returns the data that is sent in POST requests to ODC API to create a new
    certificate.
    '''
    return json.dumps({
        'jurisdiction': 'GB',
        'dataset': {
            'documentationUrl': package_url
        }
    })

def _get_auth(certs_config):
    '''
    Returns Basic Authentication user and password for ODC API.
    '''
    return (certs_config['username'], certs_config['token'])

def _get_request_path(package):
    # if package['certificate']:
    #     return '/datasets/' + package['certificate']['dataset_id'] + '/certificates'
    # else:
    #     return '/datasets'

    # ^ found out either path leads to the same outcome
    return '/datasets'

@celery.task(name='certificate.new')
def new(context, package, fetch=False):
    '''
    Creates a certificate by calling the certificate API.
    If `fetch` is true, it schedules the `certificate.fetch` task.
    '''

    # TODO: find all currently running fetch tasks for same dataset and kill them

    certs_config = context['certs_config']

    response = requests.post(
        certs_config['server'] + _get_request_path(package),
        data=_certificate_request_data(package['url']),
        auth=_get_auth(certs_config),
        headers={'content-type': 'application/json'}
    )

    if fetch:
        try:
            certs_dataset_url = response.json()['dataset_url']
            celery.send_task('certificate.fetch', args=[context, package, certs_dataset_url], task_id=make_uuid())
        except ValueError, e:
            log.error(e)

def _update_certificate(context, package, certificate):
    return requests.post(
        urljoin(context['site_url'], '/api/3/action/certificate_assign'),
        data=json.dumps({
            'id': package['id'],
            'certificate': certificate
        }),
        headers={
            'Authorization': context['apikey'],
            'content-type': 'application/json'
        }
    )

@celery.task(name='certificate.fetch', bind=True, max_retries=10, default_retry_delay=10)
def fetch(self, context, package, certs_dataset_url):
    '''
    Fetches a certificate, waiting (rescheduling itself) until the certificate is generated.
    '''

    response = requests.get(
        certs_dataset_url,
        auth=_get_auth(context['certs_config'])
    )

    try:
        log.warning(response.text)
        certs_dataset = response.json()
        success = certs_dataset['success']

        if success == True:
            certificate_json = requests.get(certs_dataset['certificate_url']).json()
            certificate = certificate_json['certificate']
            _update_certificate(context, package, certificate)
        elif success == False:
            log.info('failure')
        elif success == 'pending':
            raise self.retry()

    except ValueError, e:
        log.error(e)
