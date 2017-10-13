"""
module licenseapi.apis.SoftaculousApi
"""

import sys, pprint

from manager   import VendorManager, RequestTranslator
from webclient import UserAgentSpoofClient

from errors import StopPointReachedException, \
                   NoIdentifierProvided,      \
                   MalformedRequestError,     \
                   UnexpectedFallThroughError

class SoftaculousApi( VendorManager, UserAgentSpoofClient ):
    """
    This class is an adapter to Softaculous "NOC" service.
    Not all methods pay attention to the content of the request at this
    level -- _iCanProcessThis( item ) has already been checked.
    """
    import re, json
    import config

    ITER_LEN = 50 # max number we are getting with each request
    vendor   = 'softaculous'
    products = [ 'softaculous', ]
    urlbase  = 'https://www.softaculous.com'
    urlreq   = '/noc?nocname=%s&nocpass=%s&ca=%s'
    asklen   = '&start=%s&len=%s'

    # translate between their URL args and our request keys
    # the FIRST val in the list is the one the vendor's response will tx to.
    req_field_dict = {
        'actid'     : [ 'transaction_id' ],
        'authemail' : [ 'authemail' ],
        'autorenew' : [ 'autorenew' ],
        'date'      : [ 'transaction_date' ],
        'expires'   : [ 'expire_date' ],
        'invoid'    : [ 'invoice' ],
        'ips'       : [ 'ipaddr', 'ip', 'license_uid' ],
        'key'       : [ 'key' ],
        'license'   : [ 'serial' ],
        'licip'     : [ 'ip', 'ipaddr', 'license_uid' ],
        'lickey'    : [ 'key' ],
        'lid'       : [ 'id' ],
        'purchase'  : [ 'purchase' ],
        'servertype': [ 'server_type' ],
        'toadd'     : [ 'time_span' ], 
        'type'      : [ 'license_type' ],
        'unique'    : [ 'license_id' ],
    }
    res_field_dict = {
        'actid'     : [ 'transaction_id' ],
        'authemail' : [ 'authemail' ],
        'autorenew' : [ 'autorenew' ],
        'date'      : [ 'transaction_date' ],
        'expires'   : [ 'expire_date' ],
        'invoid'    : [ 'invoice' ],
        'ip'        : [ 'ipaddr' ],
        'ips'       : [ 'ipaddr', 'ip', 'license_uid' ],
        'key'       : [ 'key' ],
        'license'   : [ 'serial' ],
        'licip'     : [ 'ip', 'ipaddr', 'license_uid' ],
        'lickey'    : [ 'key' ],
        'lid'       : [ 'id' ],
        'purchase'  : [ 'purchase' ],
        'servertype': [ 'server_type' ],
        'toadd'     : [ 'time_span' ], 
        'type'      : [ 'license_type' ],
        'unique'    : [ 'license_id' ],
    }

    request_dict = {
        'servertype': {
            'dedicated': {
                 'servertype': '1',
            },
            'vps': {
                'servertype': '2',
            },
        },
        'autorenew': {
            'true': {
                'autorenew': '1',
            },
            'false': {
                'autorenew': '2',
            },
        },
        'ips': {
            '*': {
                'licip': '*'
            },
        },
    }
        
    response_dict = {
        'active': {
            '1': { 'active': 'true', },
            '0': { 'active': 'false', },
        },
        'server_type': {
            '1': { 'server_type': 'dedicated' },
            '2': { 'server_type': 'vps' },
        },
        'license_type': {
            '1': { 'license_type': 'dedicated' },
            '2': { 'license_type': 'vps' },
        },
        'apiuid' : {
            '*': {
                'apiuid' : None  # delete any value of apiuid
            }
        }, 
        # 'ipid' : {
            # '*': {
                # 'ipid': None
            # },
        # },
        'copyright' : {
            '*': {
                'copyright': None
            },
        },
        'expire_date': {
            '*': {
                'expire_date': lambda d: RequestTranslator._iso_to_extended( d )
            },
        },
        'transaction_date': {
            '*': {
                'transaction_date': \
                    lambda d: RequestTranslator._iso_to_extended( d ),
            },
        },
        'last_sync': {
            '*': {
                'last_sync': lambda d: RequestTranslator._iso_to_extended( d )
            },
        },
        'time': {
            '*': {
                'time': lambda d: RequestTranslator._epoch_to_iso_date( d ),
            },
        },
        'expires': { '*': { 'expires': None   } },
        # 'ip':      { '*': { 'ip'     : None   } },
        'primary': { '1': { 'primary': 'true' },
                     '2': { 'primary': 'true' },
                   },
        'unique' : { '*': { 'unique': None } },
    }
                
    # only allow access to these functions.
    # this is checked in VendorManager
    exposed = [
        '_cancel_license',  # these are part-commands for refund_license, below
        'add_license',
        'get_active_license_list',
        'get_autorenewals',
        'get_license_detail',
        'get_license_identifier',
        'get_license_list',
        'get_license_logs',
        'get_support_list',
        'modify_license'
        'refund_license',
    ]

    def __init__( self, logger=None ):
        VendorManager.__init__( self, logger=logger )
        UserAgentSpoofClient.__init__( self, self.urlbase, self.urlreq,
            self.config.CREDENTIALS[ self.vendor ][ 'username' ],
            self.config.CREDENTIALS[ self.vendor ][ 'password' ]
        )
        self.setPhpResponse()
        self.num_results = 0

    def _verify_buy( self, content ):
        """
        After RequestTranslator.subRequestFields, so in Softaculous' terms:
        """
        if len( content[ 'toadd' ] ) - 2 > 1:
            return ( False, 'time_span (too long)' )

        number, letter = (
            content[ 'toadd' ][:-1], content[ 'toadd' ][-1]
        )

        try:
            x = int( number )
        except:
            return ( False, 'toadd' )    

        if letter.upper() not in [ 'Y', 'M' ]:
            return ( False, 'toadd' )
        
        if content[ 'servertype' ] not in [ '1', '2' ]:
            return ( False, 'server_type' )
        if content[ 'autorenew' ] not in [ '1', '2' ]:
            return ( False, 'autorenew' )

        return ( True, content )

    def _verify_refund( self, content ):
        if self.translator.requestHasField( 'actid', content ):
            return ( True, content )
        return ( False, 'transaction_id is required' )

    def _verify_cancel( self, content ):
        if self.translator.requestHasField( 'lickey', content ) \
        or self.translator.requestHasField( 'licip' , content ):
            return ( True, content )
        return ( False, "Specify 'key' or 'ipaddr'" )

    def _verify_modify( self, content ):
        tx = RequestTranslator.newRequest( content,
                vendor_dict=self.field_dict
        )
        if tx.inRequest( 'ips' ) is True or tx.inRequest( 'key' ) is True:
            return ( True, content )
        return ( False, "ip address or license key is required" )

    def get_license_list( self, ignored, msg ):
        """
        Return a list of all registered licenses. Fetching them requires
        several requests since the API refuses to return more than 50.
        """
        answer = []; num_results = 0
        # prime the loop; num_results is unknown until first request returns
        self.setAppend( self.asklen % (0, self.ITER_LEN ) )
        res = self.callMethod( 'licenses' )
        num_results = res[ 'num_results' ]
        for k, r in res[ 'licenses' ].items():
            n = self.translator.subResponseFields( r )
            n = self.translator.subResponseValues( n )
            answer.append( n )

        for i in range( self.ITER_LEN, num_results, 50 ):
            self.setAppend( self.asklen % ( i, self.ITER_LEN ) )
            res = self.callMethod( 'licenses' )
            for k, r in res[ 'licenses' ].items():
                n = self.translator.subResponseFields( r )
                n = self.translator.subResponseValues( n )
                answer.append( n )
        msg.pushContent( answer )

    def get_active_license_list( self, ignored, msg ):
        """
        Return a list of active licenses only. Note that Softaculous does not
        appear to return any inactive licenses.
        """
        self.get_license_list( None, msg )
        msg.popMatching( 'active', '0' )

    def get_license_detail( self, req, msg ):
        """
        NB: It does not appear to be possible to look up a license using the
        'license' (key) field or the 'lid' field, regardless of whether you
        call method 'licenses' or 'showlicense'.
        """
        better = self.translator.subRequestFields( req )
        best   = self.translator.subRequestValues( req )
        if self.args_from_content( req ):
            data = self.callMethod( 'licenses' )
            base = data[ 'licenses' ].popitem()[ 1 ]
            subbed = self.translator.subResponseFields( base )
            subbed = self.translator.subResponseValues( base )
            msg.pushContent( subbed )
        else:
            msg.pushContent( NoIdentifierProvided(
                hint = 'Valid: ip || ipaddr || license_uid'
                )
            )

    def get_license_logs( self, req, msg ):
        """
        Return Softaculous' license log for provided key.
        """
        if self.args_from_content( req ):
            data = self.callMethod( 'licenselogs' )
            for k, v in data[ 'actions' ].items():
                tx = self.translator.subResponseFields( v )
                tx = self.translator.subResponseValues( v )
                msg.pushContent( tx )
        else:
            msg.pushContent( NoIdentifierProvided( hint = 'Valid: key || ip' ) )

    def get_autorenewals( self, req, msg ):
        """
        Return all licenses that autorenew.
        """
        answer = []; num_results = 0

        self.setAppend( self.asklen % ( 0, self.ITER_LEN ) )
        result = self.callMethod( 'renewals' )
        num_results = result[ 'num_results' ]
        for k, l in result[ 'licenses' ].items():
            tx = self.translator.subResponseFields( l  )
            tx = self.translator.subResponseValues( tx )
            msg.pushContent( tx )

        for i in range( self.ITER_LEN, num_results, 50 ):
            self.setAppend( self.asklen % ( i, self.ITER_LEN ) )
            result = self.callMethod( 'renewals' )
            for k, l in result[ 'licenses' ].items():
                tx = self.translator.subResponseFields( l  )
                tx = self.translator.subResponseValues( tx )
                msg.pushContent( tx )

    def add_license( self, req, msg ):
        """
        Purchase a license extension.
            time_span = 1M, 8M, 1Y
            server_type = 'dedicated' | 'vps'
            autorenew = 'true' | 'false'
            authemail = from config.py
            purchase = 1
        """
        req = self.translator.subRequestValues(
                self.translator.subRequestFields( req )
              )
        good, content = self._verify_buy( req )

        if good is False:
            msg.pushContent( MalformedRequestError(
                hint = 'Failed field was: %s' % content
                )
            )
            return

        content[ 'purchase'  ] = '1'
        content[ 'authemail' ] =  \
            self.config.CREDENTIALS[ 'softaculous' ][ 'authemail' ]

        if self.args_from_content( content ):
            url = self.buildURL( 'buy' )
            data = self.callMethod( 'buy' ) 
            tx = self.translator.subResponseValues(
                    self.translator.subResponseFields( data )
            )
            msg.pushContent( tx )

    def _refund_license( self, req, msg ):
        """
        Refund a license. Softaculous requires the actid ( (trans)action id )
        which is sent to us upon successful buy.
        'actid': [ 'tx_id', 'transaction_id', 'identifier' ]

        Although available through Softaculous' API, this method is not
        exposed. Our API's 'refund_license' implies _cancel_license as well.
        """
        req = self.translator.subRequestValues(
                self.translator.subRequestFields( req )
        )
        good, content = self._verify_refund( req )

        if good is False:
            msg.pushContent( MalformedRequestError(
                hint = 'Failed field was: %s' % content
                )
            )
            return

        if self.args_from_content( content ):
            url  = self.buildURL( 'refund' )
            data = self.callMethod( 'refund' ) 
            tx   = self.translator.subResponseValues(
                    self.translator.subResponseFields( data )
            )
            msg.pushContent( tx )

    def _cancel_license( self, req, msg ):
        """
        Cancel a license. Call refund first to get your money back.
        Although available through Softaculous' API, this method is not
        exposed. Our API's 'refund_license' implies _cancel_license as well.
        """
        req = self.translator.subRequestValues(
                self.translator.subRequestFields( req )
        )
        good, content = self._verify_cancel( req )

        if good is False:
            msg.pushContent( MalformedRequestError(
                hint = 'Failed field was: %s' % content
                )
            )
            return

        if self.args_from_content( content ):
            url = self.buildURL( 'cancel' )
            data = self.callMethod( 'cancel' ) 
            tx = self.translator.subResponseValues(
                    self.translator.subResponseFields( data )
            )
            msg.pushContent( tx )
 
    def refund_license( self, content, msg ):
        """
        Request a refund and cancellation in one step, which is the intention
        of our APIs refund_license request. Equivalent to refund_and_cancel in
        the PHP script.
        """
        self._refund_license( content, msg ) 
        self._cancel_license( content, msg )

    def modify_license( self, req, msg ):
        """
        Save new attrs to a current license, details of which are available
        through get_license_details method on this API.
        """
        req[ 'editlicense' ] = '1'
        good, content = self._verify_modify( msg )
        if good is False:
            msg.pushContent( MalformedRequestError(
                hint = 'Failed field was: %s' % content
                )
            )

        if self.args_from_content( content ):
            url = self.buildURL( 'showlicense' )
            data = self.callMethod( 'showlicense' ) 
            msg.pushContent( data ) 


#
# :wq
#

