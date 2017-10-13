"""
licenseapi.apis.CPanelApi
"""
import os, sys

from manager   import VendorManager, RequestTranslator
from webclient import BasicAuthPostClient
from walker    import XMLWalker

from errors import * 

class CPanelApi( VendorManager, BasicAuthPostClient ):
    """
    This class uses CPanel's Perl scripts.
    """
    import config

    vendor = 'cpanel'
    products = [ 'cpanel' ]

    urlbase = "https://manage2.cpanel.net/%s" # e.g. /XMLlicenseInfo.cgi
    urlreq  = "?output=json"

    auth_url = "https://manage2.cpanel.net"  # for urllib2.HTTPBasicAuthHandler

    commands = {
        'get_license_list': 'XML_List_Licenses.pl',
    }

    # FIXME:
    field_dict = None  # for backwards-compatibility with some code in
                       # manager.VendorManager, e.g. _getTranslator()
                       # BE SURE TO SET IT TO NONE or other dicts won't get set

    req_field_dict = {
        'ip'          : [ 'ipaddr'      ],
        # 'licenseid'   : [ 'license_id'  ],  # maybe uid
        'liscid'      : [ 'license_id'  ],
        'groupid'     : [ 'group_id'    ],
        'groupname'   : [ 'group_name'  ],
        'expiredon'   : [ 'expire_date' ],
        'newip'       : [ 'new_ip'      ],
        'packageid'   : [ 'package_id', 'package'  ],
        'packagename' : [ 'package_name' ],
        'packageqty'  : [ 'package_qty' ],
    }

    res_field_dict = {
        'ip'          : [ 'ipaddr'      ],
        'licenseid'   : [ 'license_id'  ],  # maybe uid
        'liscid'      : [ 'license_id'  ],
        'groupid'     : [ 'group_id'    ],
        'groupname'   : [ 'group_name'  ],
        'expiredon'   : [ 'expire_date' ],
        'newip'       : [ 'new_ip'      ],
        'oldip'       : [ 'ipaddr'      ],
        'packageid'   : [ 'package_id', 'package'  ],
        'packagename' : [ 'package_name' ],
        'packageqty'  : [ 'package_qty' ],
    }

    request_dict = {
        'oldip': {
            '*': {
                'ip': None,
            },
        },
        'product': {
            '*': {
                'product': None,
                'output': 'json',  # may as well since product always present
            }
        },
        'vendor': {
            '*': {
                'vendor': None,
            },
        },
    }

    response_dict = {
        'status': {
            '1': {
                'active': 'true',
                'expired': 'false',
                'expire_date': \
                     lambda d: RequestTranslator._epoch_to_iso_date( d ),
            },
            '2': {
                'active': 'false',
                'expired': 'true',
                'expire_date': \
                    lambda d: RequestTranslator._epoch_to_iso_date( d ),
            },
        },
        'adddate': {
            '*': {
                'adddate': lambda d: RequestTranslator._epoch_to_iso_date( d ),
            },
        },
        'package_id': {
            '*': {   # remove leading 'P'
                'package_id': lambda p: p[1:] if p[0] == 'P' else p 
            },
        },
        'group_id': {
            '*': {
                'group_id': lambda g: g[1:] if g[0] == 'G' else g   
            },
        },
    }

    exposed = [
        '_get_expired_licenses',
        'activate_license',
        'add_license',
        'deactivate_license',
        'get_active_license_list',
        'get_group_list',
        'get_license_detail',
        'get_license_list',
        'get_license_risk_data',
        'get_package_list',
        'get_support_list',
        'get_wiredtree_group',
        'modify_license',
    ]

    vendor_errors = {
        'License must be active.': AlreadyInactiveError,
        'This IP is already actively licensed': AlreadyActiveError,
        'is blacklisted: Internal IPs': InvalidFieldError,
        'IP is the same': InvalidFieldError,
    }

    def __init__( self, logger=None ):
        VendorManager.__init__( self, logger=logger )
        BasicAuthPostClient.__init__( self, self.urlbase, self.urlreq,
            self.config.CREDENTIALS[ self.vendor ][ 'username' ],
            self.config.CREDENTIALS[ self.vendor ][ 'password' ]
        )

    def _get_list( self, req, msg ):
        if self.args_from_content( req ) is False:
            msg.toContent( UnknownError(
                hint="args_from_content gave me False!"
                )
            )
        dikt   = json.loads( self.callMethod( 'XMLlicenseInfo.cgi' ) )
        wanted = dikt[ 'licenses' ]
        for license_id, license in wanted.items():
            better = self.translator.subResponseFields( license )
            best   = self.translator.subResponseValues( better  )
            msg.pushContent( best )

    def _getVendorError( self, errstr ):
        for e in self.vendor_errors.items():
            if e[0] in errstr:
                return e[1]( hint=errstr )
        return VendorApiError(
            hint='No such error in vendor_errors dict: %s' % errstr
        )

    def get_license_list( self, req, msg ):
        """
        Combined list of active = true and active = false.
        FYI: Combined list has ~11983 items. 
        """
        for expired in ( 0, 1 ):
            req[ 'expired' ] = expired
            self._get_list( req, msg )

    def get_active_license_list( self, req, msg ):
        req[ 'expired' ] = 0
        self._get_list( req, msg )

    def _get_expired_licenses( self, req, msg ):
        """
        Leave exposed but not an official Wiredtree API method.
        """
        req[ 'expired' ] = '2'
        self._get_list( req, msg )

    def get_license_detail( self, req, msg ):
        req = self.translator.subRequestFields( req )
        req = self.translator.subRequestValues( req )
        if self.args_from_content( req ):
            license = json.loads( self.callMethod( 'XMLRawlookup.cgi' ) )
            msg.pushContent(
                self.translator.subResponseValues(
                    self.translator.subResponseFields( license )
                )
            )
        else:
            msg.pushContent(
                MalformedRequestError(
                    hint="Get arguments could not be parsed from request provided"
                )
            )

    def get_license_risk_data( self, req, msg ):
        """
        Calling this function returns:
        {u'reason': u'wiredtree is not allowed to access secverify.',
               u'status': 0}
        """
        req = self.translator.subRequestFields( req )
        req = self.translator.subRequestValues( req )
        if not self.translator.requestHasField( 'ip', req ):
            msg.pushContent(
                NoIdentifierProvided( hint='missing ipaddr' )
            )
            return
        if self.args_from_content( req ):
            license = json.loads( self.callMethod( 'XMLsecverify.cgi' ) )
            msg.pushContent(
                self.translator.subResponseValues(
                    self.translator.subResponseFields( license )
                )
            )
        else:
            msg.pushContent(
                MalformedRequestError(
                    hint="GET args could not be parsed from request."
                )
            )

    def get_group_list( self, ignored, msg ):
        """
        Fetch wiredtree's group information from Cpanel.
        """
        groups = json.loads( self.callMethod( 'XMLgroupInfo.cgi' ) )[ 'groups' ]
        for group_id, group_name in groups.items():
            res = self.translator.subResponseValues(
                    { 'group_id': group_id,
                      'group_name': group_name
                    }
            )
            msg.pushContent( res )

    def get_wiredtree_group( self, ignored, msg ):
        """
        May or may not prove to be a cute shortcut
        """
        groups = json.loads( self.callMethod( 'XMLgroupInfo.cgi' ) )[ 'groups' ]
        for group_id, group_name in groups.items():
            if group_name.decode() == 'WiredTree*':
                res = self.translator.subResponseValues(
                        { 'group_id': group_id,
                          'group_name': group_name
                        }
                )
                msg.pushContent( res )

    def get_package_list( self, ignored, msg ):
        pkgs = json.loads(
                 self.callMethod( 'XMLpackageInfo.cgi' )
               )[ 'packages' ]
        for package_id, package_name in pkgs.items():
            res = self.translator.subResponseFields(
                { self.translator.getOurFieldFor( 'packageid' ): package_id,
                  self.translator.getOurFieldFor( 'packagename' ): package_name,
                }
            )
            res = self.translator.subResponseValues( res )
            msg.pushContent( res )

    def add_license( self, req, msg ):
        needed = [ 'groupid', 'packageid', 'ip' ]
        if self.translator.requestFillsFields( needed, req ) is True:
            req[ 'reactivateok' ] = '1'
            req[ 'force'        ] = '1'
            req = self.translator.subRequestFields( req )
            req = self.translator.subRequestValues( req )  
            # result = json.loads( self.callMethod( 'XMLlicenseAdd.cgi' ) )
            # better = self.translator.subResponseFields( result )
            # best   = self.translator.subResponseValues( better )
            # msg.pushContent( best )
            msg.pushContent( NoError() )
        else:
            msg.pushContent( MalformedRequestError(
                hint = 'cpanel requires ipaddr, group_id and package_id ' \
                       'to add_license'
                )
            )

    def deactivate_license( self, req, msg ):
        """
        Cpanel's 'Expire License' feature.
        """
        # needed = [ 'ip', 'groupid', 'packageid' ]
        needed = [ 'groupid', 'packageid' ]
        if self.translator.requestFillsFields( needed, req ) is True:
            del req[ 'vendor'  ]
            del req[ 'product' ]

            req[ 'reason' ] = 'WiredTree internal API method call'
            req[ 'output' ] = 'json'

            req = self.translator.subRequestFields( req )
            req = self.translator.subRequestValues( req )  

            # hack for inconsistent names across Cpanel's method calls
            if 'licenseid' in req.keys():
                req[ 'liscid' ] = req[ 'licenseid' ]
                del req[ 'licenseid' ]

            res = json.loads( self.postMethod( 'XMLlicenseExpire.cgi', req ) )
            better = self.translator.subResponseFields( res    )
            best   = self.translator.subResponseValues( better )

            if best[ 'status' ] > 0:
                msg.pushContent( best )
            else:
                msg.pushContent(
                    self._getVendorError( best[ 'reason' ] )
                )

        else:
            msg.pushContent( MalformedRequestError(
                hint = 'cpanel requires ipaddr, group_id and package_id to deactivate'
                )
            )

    def activate_license( self, req, msg ):
        """
        Re(activate) Cpanel license
        """
        needed = [ 'groupid', 'packageid', 'ip' ]
        if self.translator.requestFillsFields( needed, req ) is True:
            del req[ 'vendor' ]
            del req[ 'product' ]
            req[ 'reactivateok' ] = 1
            req[ 'force'        ] = 0 
            req[ 'output'       ] = 'json'

            req = self.translator.subRequestFields( req )
            req = self.translator.subRequestValues( req )

            res = json.loads( self.postMethod( 'XMLlicenseAdd.cgi', req ) )
            better = self.translator.subResponseFields( res    )
            best   = self.translator.subResponseValues( better )

            if best[ 'status' ] > 0:
                msg.pushContent( best )
            else:
                msg.pushContent(
                    self._getVendorError( best[ 'reason' ] )
                )
        else:
            msg.pushContent( MalformedRequestError(
                hint = 'cpanel activate requires group_id, package_id, ipaddr'
                )
            )

    def modify_license( self, req, msg ):
        """
        Call Cpanel "Transfer" method to transfer IP address.
        """
        needed = [ 'groupid', 'packageid', 'ip', 'newip' ]
        if self.translator.requestFillsFields( needed, req ) is True:
            
            req = self.translator.subRequestFields( req )
            req = self.translator.subRequestValues( req )

            test = self._postEncode( req )

            res = json.loads( self.postMethod( 'XMLtransfer.cgi', req ) )
            better = self.translator.subResponseFields( res    )
            best   = self.translator.subResponseValues( better )

            if best[ 'status' ] > 0:
                msg.pushContent( best )
            else:
                msg.pushContent(
                    self._getVendorError(
                        best[ 'reason' ] )
                )


#
# :wq
#

