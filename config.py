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
    { 'username': 'yourcompany',
      'password': 'vC2ZdwxxvudskH4N'
    },
    'litespeed': {
        'username': 'support@yourcompany.com',
        'password': 'u7MeSwzUBbAFkH4N',
    },
    'softaculous': {
        'username' : 'yourcompany',
        'password' : '9nuh5N7Yjxi8kH4N',
        'authemail': 'somebody@yourcompany.com'  # required by softaculous
    },
    'cpanel': {
        'username': 'yourcompany',
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
