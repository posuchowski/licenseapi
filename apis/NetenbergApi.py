"""
module licenseapi.apis.NetenbergApi
"""

import sys, codecs, pprint

from soap import SudsClient
from manager import VendorManager, RequestTranslator
from errors import *

class NetenbergApi( VendorManager, SudsClient ):
    '''
    The reward: the ability to write really boring code.
    '''
    import config
    import md5
    
    vendor   = 'netenberg'
    products = [ 'fantastico' ]
    wsdl = 'https://netenberg.com/api/netenberg.wsdl'

    req_field_dict = {
        'ip': [ 'ipaddr' ]
    }
    res_field_dict = req_field_dict

    response_dict = request_dict = {}

    exposed = [
        'get_support_list',
        'get_license_identifier',
        'get_license_list',
        'get_active_license_list',
        'get_license_detail',
        'deactivate_license',
        'activate_license'
    ]

    soapImports = ( 'http://www.w3.org/2001/XMLSchema',
                    'http://www.w3.org/2001/XMLSchema.xsd'
                  )

    def __init__( self, logger=None ):
        VendorManager.__init__( self, logger=logger )
        SudsClient.__init__( self, self.wsdl, imports=self.soapImports )

        self.username   = self.config.CREDENTIALS[ self.vendor ][ 'username' ]
        self.password   = self.config.CREDENTIALS[ self.vendor ][ 'password' ]

        self._makeCred()
        # self._makeSoap()

    def _makeCred( self ):
        cred_hash = self.md5.new()
        cred_hash.update( self.username + self.password )
        self.cred_hash = cred_hash.hexdigest()

    def get_license_list( self, ignored, msg ):
        try:
            iplist = self.soap.getIpList( self.cred_hash, 0 )
        except Exception as E:
            sys.stderr.write( "An Exception occurred: " )
            sys.stderr.write( repr(E) ); sys.stderr.write( '\n' )
            msg.pushContent( VendorApiError(
                hint='Call to Netenberg SOAP API failed.'
                )
            )
            return 
        for ip in iplist:
            if ip is None: continue
            msg.pushContent( self.buildContent( { 'ipaddr': ip } ) )

    def get_active_license_list( self, ignored, msg ):
        self.setSoapPort( 'getJSONListPort' )
        iplist = self.soap.getJSONList( self.cred_hash, 0 )
        pprint.pprint( iplist )
        msg.pushContent( self.BOGUS )

    def get_license_detail( self, req, msg ):
        if self.translator.requestFillsField( 'ip', req ):
            ip = self.translator.getRequested( 'ip', req )
        self.setSoapPort( 'getIpDetailsPort' )
        res = self.soap.getIpDetails( self.cred_hash, ip )
        msg.pushContent( self.BOGUS )

    def get_license_logs( self, req, msg ):
        msg.pushContent( NoVendorAnalogError(
            hint='Netenberg has no per-ipaddr logs.'
            )
        )

    def deactivate_license( self, req, msg ):
        self.setSoapPort( 'deactivateIpPort' )
        result = self.soap.deactivateIp( self.cred_hash, req[ 'ipaddr' ] )
        pprint.pprint( result )
        msg.pushContent( self.BOGUS )

    def activate_license( self, req, msg ):
        self.setSoapPort( 'reactivateIpPort' )
        result = self.soap.reactivateIp( self.cred_hash, req[ 'ipaddr' ] )
        pprint.pprint( result )
        msg.pushContent( self.BOGUS )

    def get_autorenewals( self, req, msg ):
        pass


#
# :wq
#

