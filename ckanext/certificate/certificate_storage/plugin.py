import json
import urlparse
import ckan.plugins as p
import ckan.logic as logic
from ckan.plugins import toolkit
from ckan.lib.celery_app import celery
from ckan.model.types import make_uuid
from logging import getLogger

log = getLogger(__name__)

def certificate_assign(context, data_dict):

    # Raises toolkit.NotAuthorized if user is not authorised to perform an update.
    # Avoiding it for now as a disabled sysadmin user is detected.
    toolkit.check_access('package_update', context, {'id': data_dict['id']})

    # `get_or_bust` documentation:
    # http://ckan.readthedocs.org/en/ckan-2.3.1/extensions/plugins-toolkit.html#ckan.plugins.toolkit.get_or_bust
    id = logic.get_or_bust(data_dict, 'id')
    certificate = logic.get_or_bust(data_dict, 'certificate')

    model = context['model']
    package = model.Package.get(id)

    # Raising 404s should ideally not be handled manually, but couldn't find
    # something like get_or_404.
    if not package:
        raise toolkit.ObjectNotFound

    model.repo.new_revision()
    package.extras['certificate'] = json.dumps(certificate)
    model.Session.commit()

    return logic.get_action('package_show')(context, {'id': id})

class CertificateStorage(p.SingletonPlugin):

    p.implements(p.IActions)

    # IActions

    def get_actions(self):
        return {'certificate_assign': certificate_assign}
