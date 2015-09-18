# Open Data Certificate extension for CKAN

The extension contains 2 plugins:

1. **auto_certification**: creates a new certificate whenever a dataset is added or updated
2. **certificate_storage**: provides an action (externally accessible via POST request) for updating the certificate stored for a dataset


## Installation

Download the plugin in the folder you keep CKAN extensions (can be any folder), then open a terminal in the `ckanext-certificate` folder. Enable your Python virtual environment for CKAN and run:

```
pip install -r pip-requirements.txt
python setup.py develop
```

This will install the extension in your virtual environment. To activate the plugins, you will need to open your CKAN configuration file (usually in `/etc/ckan/default/production.ini`) and append `auto_certification` and `certificate_storage` to the `ckan.plugins` line.
