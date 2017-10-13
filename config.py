#
# conf.py : API configuration
#

# Directory where api handlers live
API_DIRECTORY = '/home/peter/src/license_service/licenseapi/apis'

# List your vendor api handler here
APIS = { 'nullvendor': 'NullApi',
         'netenberg': 'NetenbergApi',
         'litespeed': 'LiteSpeedApi',
         'softaculous': 'SoftaculousApi',
         'cpanel': 'CPanelApi'
}

# These are the foreign API credentials.
CREDENTIALS = {
    'netenberg':
    { 'username': 'wiredtree',
      'password': 'vC2ZdwxxvudskH4N'
    },
    'litespeed': {
        'username': 'support@wiredtree.com',
        'password': 'u7MeSwzUBbAFkH4N',
    },
    'softaculous': {
        'username' : 'wiredtree',
        'password' : '9nuh5N7Yjxi8kH4N',
        'authemail': 'posuchowski@wiredtree.com'  # required by softaculous
    },
    'cpanel': {
        'username': 'wiredtree',
        'password': 'ABydEu7njPqTkH4N',
    },
}

DB = {
    'ubersmith': {
        'hostname': 'localhost',
        'username': 'licenseweb',
        'password': 'htimsrebeu',
    }
}
