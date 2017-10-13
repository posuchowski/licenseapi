"""
LiteSpeedApi
"""
import sys

from errors    import *
from manager   import VendorManager, RequestTranslator
from webclient import UserAgentSpoofClient
from walker    import XMLWalker

class LiteSpeedApi( VendorManager, UserAgentSpoofClient ):
    """
    This class is an adapter to LiteSpeed's License API.
    """
    import re, json
    import config

    vendor   = 'litespeed'
    products = [ 'LSWS' ]
    urlbase  = 'https://store.litespeedtech.com'
    urlreq   = '/reseller/LiteSpeed_eService.php' \
               '?litespeed_store_login=%s&litespeed_store_pass=%s' \
               '&eService_version=1.1&eService_action=%s'

    # Litespeed has 2 or even 3 names for certain fields depending on the
    # function called. Problems in translation can often be fixed in
    # the request_dict or response_dict, without writing a special function.

    # 'theirs': [ 'ours', 'ours', ... ]
    field_dict = {
        'ip'             : [ 'ipaddr', 'license_uid' ],
        'license_ip'     : [ 'ipaddr', 'license_uid' ],
        'server_ip'      : [ 'ipaddr', 'license_uid' ],
        'id'             : [ 'id' ],
        'license_id'     : [ 'id' ],
        'serial'         : [ 'serial', 'license_uid' ],
        'license_serial' : [ 'serial', 'license_uid' ],
        'type'           : [ 'server_type'  ],
        'license_type'   : [ 'license_type' ],
        'status'         : [ 'active'       ],
        'order_payment'  : [ 'payment_type' ],
        'order_cvv'      : [ 'payment_cvv'  ],
        'order_promocode': [ 'promocode'    ],
        'order_cpu'      : [ 'cpus'         ],
        'order_period'   : [ 'time_span'    ],
        'order_product'  : [ 'product'      ],
        'product'        : [ 'order_product'],
        'license_expire_date' : [ 'expire_date' ],
        'license_update_expire_date': [ 'expire_date' ],
    }
    req_field_dict = res_field_dict = None

    # Individual substitutions (innermost dict) can hold lambdas
    # as well as literals. keep in mind that the value substitution is
    # made AFTER the field substitution (that uses field_dict above ).
    # See code and comments for RequestTranslator.substitute() and friends.
    # Lambdas recieve the original field value and return the new value.
    response_dict = {
        'license_type': {                   # if 'type' ==
              'WS_L_V': {                   # 'WS_L_V':
                'license_type': 'vps',      #    license_type = vps
                'server_type': 'vps',       #    server_type  = vps
                'cpus': None,               #    del response[ 'cpus' ]
              },                            
              'WS_L_1': {
                'license_type': 'cpu',
                'cpus': '1',
                'server_type': 'dedicated',
              },
              'WS_L_2': {
                'license_type': 'cpu',
                'cpus': '2',
                'server_type': 'dedicated', 
              },                            
              'WS_L_4': {
                'license_type': 'cpu',
                'cpus': '4',
                'server_type': 'dedicated', 
              },
              'WL_L_8': {
                'license_type': 'cpu',
                'cpus': '8',
                'server_type': 'dedicated', 
              },
        },
        'server_type': {
              'WS_L_V': {      
                'server_type': 'vps',
                'license_type': 'vps',
              },
              'WS_L_1': { 
                'server_type': 'dedicated',
                'license_type': 'cpu',
                'cpus': '1',
              }, 
              'WS_L_2': {
                'server_type': 'dedicated',
                'license_type': 'cpu',
                'cpus': '2',
              },
              'WS_L_4': {
                'server_type': 'dedicated',
                'license_type': 'cpu',
                'cpus': '4',
              },
              'WL_L_8': {
                'server_type': 'dedicated',
                'license_type': 'cpu',
                'cpus': '8',
              },
        },
        'active': {
            'Active': {
                'active': 'true',
            },
            'Inactive': {
                'active': 'false',
            }
        },
    }

    # This dictionary functions as the other, above, but is used to translate
    # values sent to us by our clients.
    request_dict = {
        'order_payment': {                     # if order_payment == 
            'card': {                          #    'card' then
                'order_payment': 'creditcard', # order_payment = 'creditcard'
            },
        },
        'order_period': {
            '1M': {
                'order_period': 'monthly',
            },
            '1Y': {
                'order_period': 'yearly',
            },
        },
        'license_type': {
            'vps': {
                'order_cpu': 'V',
                'license_type': None,  # delete this field from request
            },
            'dedicated': {
                'license_type': None,
            },
        },
        'vendor': {
            '*': {
                'vendor': None
            },
        },
        'type': {
            'vps': {
                'order_cpu': 'V',
                'type': None,
            },
        },
    }

    exposed = [
        'add_license',
        'deactivate_license',
        'get_active_license_list',
        'get_license_detail',
        'get_license_identifier',
        'get_license_list',
        'get_license_logs',
        'get_support_list',
        'refund_license',
    ]

    def __init__( self, logger=None ):
        VendorManager.__init__( self, logger=logger )
        UserAgentSpoofClient.__init__( self, self.urlbase, self.urlreq,
            self.config.CREDENTIALS[ self.vendor ][ 'username' ],
            self.config.CREDENTIALS[ self.vendor ][ 'password' ]
        )
        self.translator = RequestTranslator(
            field_dict    = self.field_dict,
            request_dict  = self.request_dict,
            response_dict = self.response_dict,
            validator     = None
        )

    def _xml2json( self, raw ):
        """
        Convert LiteSpeed's XML to a list of dictionaries. Just parse the text
        because there isn't an XML structure within the <message>.
        """
        json_content = []
        for line in raw.split('\n'):
            if ':' not in line: continue  # discard some XML at top & bottom
            line = self.re.sub( r"<.*>", "", line ).lstrip()

            # A complete out line breaks into 10 tokens, but (at least)
            # the last one doesn't.
            tokens   = self.re.split( '[: ]', line )
            lic_type = tokens.pop( 0 )

            # Only ip appears to be misssing in len == 8 lines, but who knows?
            lic_id = lic_ip = l_serial = None
            while tokens:
                n = tokens.pop( 0 )
                if n == 'id':
                    lic_id = tokens.pop( 0 ).strip( '()'  )
                elif n == 'ip':
                    lic_ip = tokens.pop( 0 ).strip( '()'  )
                elif n == 'serial':
                    l_serial = tokens.pop( 0 ).strip( '(),' )
                else:
                    continue
                    
            json_content.append(
                { 'type'  : lic_type,
                  'id'    : lic_id,
                  'ip'    : lic_ip,
                  'serial': l_serial
                }
            )
        return json_content

    def get_license_list( self, ignored, msg ):
        """
        LiteSpeed only has hardcoded query_field=AllActiveLicenses
        Perhaps someone should contact them, since they claim they'll
        implement popular desiderata.
        """
        self.get_active_license_list( ignored, msg )
        # msg.pushContent( NoVendorAnalogError(
            # hint = "LiteSpeed only supports 'get_active_license_list'"
            # )
        # )

    def get_license_detail( self, req, msg ):
        self.setAppend( "&query_field=LicenseDetail_IP:%s" %
            self._getTranslator().getRequested(
                self._getTranslator().getTheirRequestFieldFor( 'ipaddr' ),
                req
            )
        )
        result = self.callMethod( 'Query' )
        cooked = XMLWalker( result ).toDict()
        self.translator.subResponseFields( cooked )
        self.translator.subResponseValues( cooked )
        if cooked is not None:
            msg.pushContent( cooked )
        else:
            msg.pushContent(
                ShouldNotBeNone( "Expected a dict but got None instead." )
            )

    def get_active_license_list( self, ignored, msg ):
        """
        Return a list of all active licenses.
        """
        answer = []
        raw = self.callMethod( 'Query&query_field=AllActiveLicenses' )
        json_list = self._xml2json( raw )
        for item in json_list:
            answer.append( self.translator.subResponseValues(
                self.translator.subResponseFields( item )
                )
            )
        msg.pushContent( answer )

    def get_license_logs( self, ignored, msg ):
        """
        Also not supported by LiteSpeed as of this writing.
        """
        msg.pushContent( NoVendorAnalogError(
            hint = "LiteSpeed does not support fetching license logs."
            )
        )

    def get_autorenewals( self, ignored, msg ):
        """
        Also not supported by LiteSpeed as of this writing.
        """
        msg.pushContent( NoVendorAnalogError(
            hint = "LiteSpeed does not support fetching license logs."
            )
        )

    def add_license( self, req, msg ):
        """
        Buy a license.
        """
        # req[ 'order_product' ] = msg.findProduct()
        
        req = self.translator.subRequestFields( req )
        req = self.translator.subRequestValues( req )

        if self.args_from_content( req ) is False:
            sys.stderr.write( "\nWHOA!!! args_from_content returned False!!\n" )
            msg.pushContent( 
                    YouShouldNotBeSeeingThisError(
                        hint = 'WebClient.args_from_content() returned False.'
                    )
            )
        raw = self.callMethod( 'Order' )
        real = XMLWalker( raw ).toDict()
        trans = self.translator.subResponseValues(
                    self.translator.subResponseFields( real )
                )
        msg.pushContent( trans )

    def refund_license( self, req, msg ):
        """
        Cancel purchased license.
        """
        req[ 'cancel_now' ] = 'Y'
        req[ 'order_product' ] = None

        req = self.translator.subRequestFields( req )
        req = self.translator.subRequestValues( req )
        self.args_from_content( req )
        get = self.callMethod( 'Cancel' )
        data = XMLWalker( get ).toDict()
        data = self.translator.subResponseValues(
                 self.translator.subResponseFields( data )
               )
        msg.pushContent( data )

    def deactivate_license( self, req, msg ):
        self.refund_license( req, msg )
        

#
# :wq
#

