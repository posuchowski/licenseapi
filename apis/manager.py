#
# module licenseapi.apis.manager: VendorManager, RequestTranslator
#

import sys, types, datetime

from errors import ApiError, NoSuchFunctionError, NoSuchProductError, \
   StopPointReachedException, MalformedRequestError

class VendorManager( object ):
    '''
    API interface class (ancestor of all specific vendor managers).
    '''
    BOGUS    = { 'nokey': 'novalue' }
    vendor = None
    products = []
    logger = None

    exposed = [ ] # nothing by default

    def __init__( self, logger=None, DEBUG=True ):
        self.DEBUG = DEBUG
        if logger is None:
            self.logger = sys.stderr
        else:
            self.logger = logger
        self.translator = None
        self.translator = self._getTranslator()  # premake a copy
        self._ensure_implementation()

    # Enforce my idealistic vision on everyone else
    def _ensure_implementation( self ):
        if hasattr( self, 'field_dict' ) is False:
            if hasattr( self, 'req_field_dict' ) is False \
                or hasattr( self, 'res_field_dict' ) is False:
                raise NotImplementedError(
                    "self.field_dict not present in subclass"
                )
        if hasattr( self, 'request_dict' ) is False:
            raise NotImplementedError(
                "self.request_dict not present in subclass"
            )
        if hasattr( self, 'response_dict' ) is False:
            raise NotImplementedError(
                "self.response_dict not present in subclass"
            )
        if self.exposed == []:
            raise NotImplementedError(
                "No methods exposed! self.exposed = []"
            )

    def _iCanProcessThis( self, item ):
        v = item[ 'vendor' ]
        if v != self.vendor:
            return False

        p = item[ 'product' ]
        if p == '__all__' or p == '__none__':
            return True

        if p not in self.products:
            return False
        return True

    def _getTranslator( self ):
        if self.translator is None:
            return RequestTranslator(
                # field_dict = self.field_dict,
                req_field_dict = self.req_field_dict,
                res_field_dict = self.res_field_dict,
                request_dict = self.request_dict,
                response_dict = self.response_dict
            )
        else:
            return self.translator

    def buildContent( self, dikt, product=None ):
        product = self.products[0] if product is None else product
        content = { 'vendor': self.vendor, 'product': product }
        content.update( dikt )
        return content
            
    def myVendor( self ):
        return self.vendor

    def myProducts( self ):
        return self.products

    def get_support_list( self, item, msg ):
        for p in self.products:
            msg.pushContent(
                { 'vendor' : self.vendor,
                  'product': p
                }
            )

    def get_license_identifier( self, item, msg ):
        """
        Note that RequestTranslator doesn't currently support multiple products
        """
        for p in self.products:
            msg.pushContent(
              {
                'vendor'    : self.vendor,
                'product'   : p,
                'identifier': ",".join( self.translator.getAllTheirFieldsFor( 'license_uid' ) ),
                'value'     : "See API documentation",
              }
            )
                
    def processItem( self, item, message ):
        method = message.getMethod()
        if method not in self.exposed:
            message.pushContent( NoSuchFunctionError( hint = method ) )
            return

        if self._iCanProcessThis( item ):
            m = getattr( self, method )
            m( item, message )
        else:
            message.pushContent( NoSuchProductError(
                hint = '%s products are: %s' %
                    ( self.vendor, ",".join( self.products ) )
                )
            )

    def txGetTx( self, method, req ):
        """
        Shortcut to translate request into vendor terms,
        call the remote method, and translate the results
        back into our terms before returning them.
        """
        req = self.translator.subRequestValues(
                self.translator.subRequestFields( req )
        )
        if self.args_from_content( content ):
            res = self.callMethod( 'cancel' )
            res = self.translator.subResponseValues(
                    self.translator.subResponseFields( res )
            )
            return res
        else:
            return MalformedRequestError(
                hint = "Programming error: call to WebClient." \
                       "args_from_content failed!"
            )



class RequestTranslator( object ):
    """
    RequestTranslator( <field_dict:dict>, <response_dict:dict>, <validator:func> )
        
    Where:
        field_dict =
            { 'theirFieldName': [ 'ourPossibleName1' , 'ourPossibleName2', ... ] }
        response_dict =
            { 'theirField':
                { 'theirValue': 'ourValue' } ,
                ... ,
            }
        # pass a function that validates requests
        validator = function( request ) -> Boolean
            
    A class to translate between our fields and the remote API's fields.
    Also to mangle return values into our value names.  Does not store
    requests or responses, these are passed into the various lookup functions.
    """
    def __init__( self, field_dict=None, req_field_dict=None,
                  res_field_dict=None, request_dict=None,
                  response_dict=None, validator=None          ):

        self.field_dict    = field_dict     # a dict of lists

        # allow for separate request and response fields, for the
        # case where vendors switch up names to fool you
        if req_field_dict is None:
            self.req_field_dict = field_dict
        else:
            self.req_field_dict = req_field_dict
        if res_field_dict is None:
            self.res_field_dict = field_dict
        else:
            self.res_field_dict = res_field_dict

        self.response_dict = response_dict 
        self.request_dict = request_dict 
        self.validator = validator  

    def newResponse( self, response, field_dict=None ):
        """
        Get an object with a copy of field_dict but new response content.
        """
        if field_dict is None:
            field_dict = self.field_dict
        return RequestTranslator( response=response, field_dict=field_dict )

    # Statics for lamda translations

    @staticmethod
    def _epoch_to_iso_date( epoch_time ):
        seconds = float( epoch_time )
        return str( datetime.date.fromtimestamp( seconds ) )

    @staticmethod
    def _iso_to_extended( datestr ):
        """
        Takes basic ISO 8601 YYYYMMDD and
        Returns ISO 8601 Extended Date format: YYYY-MM-DD
        """
        yyyy = datestr[0:4]
        mm   = datestr[4:6]
        dd  = datestr[6:]
        return "%s-%s-%s" % ( yyyy, mm, dd )


    # Fieldname resolution operations: Retrive our field name(s) from their names.

    def getOurFieldFor( self, theirs ):
        """
        getOurFieldFor( theirFieldName:str ) -> ourFieldName:str

        Return the first value in the list only. But now we have to check other
        things.
        """
        try:
            return self.req_field_dict[ theirs ][0]
        except:
            pass
        try:
            return self.res_field_dict[ theirs ][0]
        except:
            pass
        try:
            return self.field_dict[ theirs ][0]
        except:
            return None

    def getTheirResponseFieldFor( self, our ):
        """
        This method is meant to be called when sending a request, so it will
        check the req_field_dict first in the interst of efficiency.
        """
        for k, v in self.res_field_dict.items():
            if our in v:
                return k
        return None

    def getTheirRequestFieldFor( self, our ):
        """
        What do they call their field?
        """
        for k, v in self.req_field_dict.items():
            if our in v:
                return k
        return None

    def getAllTheirFieldsFor( self, ours ):
        results = []
        for k, v in self.req_field_dict.items():
            if ours in v:
                results.append( k )
        for k, v in self.res_field_dict.items():
            if ours in v:
                results.append( k )
        for k, v in self.field_dict.items():
            if ours in v:
                results.append( k )
        return results or None

    def getAllOurFieldsFor( self, theirs ):
        results = []
        try:
            results.extend( self.req_field_dict[ theirs ] )
        except:
            pass
        try:
            results.extend( self.res_field_dict[ theirs ] )
        except:
            pass
        try:
            results.extend( self.field_dict[ theirs ] )
        except:
            pass
        return results or None

    def getAllOurReqFieldsFor( self, theirs ):
        """
        As above but only use the request field dictionary, req_field_dict
        """
        try:
            return self.req_field_dict[ theirs ]
        except:
            return None

    def getAllOurResFieldsFor( self, theirs ):
        """
        As above but only use the response field dictionary, res_field_dict
        """
        try:
            return self.res_field_dict[ theirs ]
        except:
            return None

    def getAllTheirFieldNames( self ):
        """
        All their field is belong to us
        """
        results = []
        results.extend( self.req_field_dict.keys() )
        results.extend( self.req_field_dict.keys() )
        results.extend( self.req_field_dict.keys() )
        results.sort()
        return results or None

    # Field value retrieval

    def getReponseValueFor( self, theirs, response ):
        """
        Return a response's value using their name as key.
        """
        if self.responseHasField( theirs ):
            return response[ theirs ]
        return None
        
    def getResponseValueForOur( self, ours, reponse ):
        """
        Return a response's value using our field name as the key.
        """
        key = self.getTheirResponseFieldFor( ours )
        if key is None:
            return None
        return self.getResponseValueFor( key )

    # Request ( outgoing ) methods: check or get

    def substitute( self, sub, res ):
        """
        substitute( self, dict, dict ): Operate in-place on dict res

        Where:
            sub: dictionary of key/value substitution pairs
                 or key/lambda pairs.
            res: the response dictionary to update
        """
        for k, v in sub.items():
            if type( v ) == types.StringType:
                res[ k ] = v
            elif type( v ) == types.FunctionType:  # run res[k] through lambda
                if k in res.keys():
                    res[ k ] = v( res[ k ] )           
                else:
                    try:
                        res[ k ] = v()
                    except TypeError:
                        res[ k ] = None
            elif type( v ) == types.NoneType:
                if k in res.keys():
                    del res[ k ]
            else:
                raise ValueError( "_doResponseSubs: sub dictionary has " \
                    "unsupported type '%s' for key '%s'" % ( type( v ), k )
                )

    def subSplats( self, res=None, req=None ):
        """
        Asterisk (the Splat) matches all values.

        A translation dictionary entry of the form:
            'field': { '*': { 'other': 'value' || None }}  or even
            'field': { '*': { 'other': '*' }}
        is handled in this function.

        The second mechanism provides a way to switch original vals to a new
        key. E.g. the subdict:
            'field1': {
                '*': {
                    'otherfield': '*'
                }
            }
        results in the following switch:
            request[ otherfield ] = request[ field1 ]
        """
        if req is not None:
            source = self.request_dict
            dikt = req
        elif res is not None:
            source = self.response_dict
            dikt = res
        else:
            raise ValueError(
                "RequestTranslator.subSplats(): must get one of res or req!"
            )
        for key, val in source.items():
            # e.g. tuple = ( 'apiuid', { '*': { 'apiuid': None } } )
            if key not in dikt.keys():
                continue
            for innerK, innerV in val.items():
                # ( '*', { 'apiuid': None } )
                if innerK == '*':
                    for k, v in innerV.items():
                        # ( 'apiuid', None )
                        if v is None:
                            if k in dikt.keys():
                                del dikt[ k ]
                        elif v == '*':
                            dikt[ k ] = dikt[ key ]
                        elif type( v ) == types.FunctionType:
                            if k in dikt.keys():
                                dikt[ k ] = v( dikt[ k ] )           
                            else:
                                try:
                                    dikt[ k ] = v()
                                except TypeError:
                                    res[ k ] = None
                        else:
                            dikt[ k ] = v
        return dikt

    def subResponseFields( self, res ):
        # first things first: handle the splat
        for theirName in self.res_field_dict.keys():
            if theirName in res.keys():
                if res[ theirName ] == None:
                    del res[ theirName ]
                    continue
                match = self.getAllOurResFieldsFor( theirName )
                if match is not None:
                    saved = res[ theirName ]
                    del res[ theirName ]
                    if len( match ) == 1:
                        res[ match[0] ] = saved
                    else:
                        for ourName in match:
                            res[ ourName ] = saved
            else:
                continue
        return res

    def subRequestFields( self, req ):
        for ourName in req.keys():
            # sys.stderr.write( "\t'%s' " % ourName )
            field = self.getTheirRequestFieldFor( ourName )
            if field is not None:
                # sys.stderr.write( " -> %s\n" % field )
                req[ field ] = req[ ourName ]
                del req[ ourName ]
            else:
                continue
        return req

    def subResponseValues( self, res ):
        res = self.subSplats( res=res )
        for field in self.response_dict.keys():
            if self.responseHasField( field, res ) is True:
                for val, sub_dict in self.response_dict[ field ].items():
                    if res[ field ] == val:
                        self.substitute( sub_dict, res )
        return res

    def subRequestValues( self, req ):
        req = self.subSplats( req=req )
        for field in self.request_dict.keys():
            if self.requestHasField( field, req ) is True:
                for val, sub_dict in self.request_dict[ field ].items():
                    if req[ field ] == val:
                        self.substitute( sub_dict, req )
        return req

    def getRequested( self, their, request ):
        """
        getRequested( theirFieldName, dict ) -> ourFieldValue

        Retrieve a Request's value for a vendor's field, from the provided dict
        e.g. Given: request = { 'ipaddr': '10.0.0.1' ... }
             And  : field_dict = { 'ip' : [ 'ipaddr', 'ip', ... ] }
             Then : self.getRequested( 'ip' ) == '10.0.0.1'
        """
        if request is None: return None
        possible = self.getAllOurReqFieldsFor( their )
        if possible is not None:
            for f in possible:
                if f in request.keys():
                    return request[ f ]
        return None

    def requestFillsField( self, field, request ):
        """
        requestFillsField( theirFieldName ) -> Boolean

        Does our request have an attribute that can fill their 'field'?
        This checks against the request field dictionary, req_field_dict
        """
        if request is None: return False
        allpossible = self.getAllOurReqFieldsFor( field )
        sys.stderr.write( "RT.requestFillsField: checking for %s in %s\n" % \
            ( field, str( allpossible ) )
        )
        for f in allpossible:
            if f in request.keys():
                return True
        return False

    def requestFillsFields( self, field_list, request ):
        """
        Shortcut for running a list thru above.
        """
        for f in field_list:
            if self.requestFillsField( f, request ) is False:
                return False
        return True


    def responseHasField( self, field, response ):
        """
        responseHasField( theirFieldName ) -> Boolean

        Is their FieldName present in the response keys?
        """
        if response is None:
            return False
        if field in response.keys():
            return True
        return False

    def requestHasField( self, field, request ):
        """
        requestHasField( ourFieldName ) -> Boolean

        Did our user deign to grace us with this 'field'?
        """
        if request is None:
            return False
        if field in request.keys():
            return True
        return False
        
    def responseIsError( self, response, checker=None ):
        """
        responseIsError( response [, checker:function ] ) -> Boolean

        Check if a response is an error. Either use a checker
        func registered in __init__, passed into this, or default
        to checking that an 'error' field is not None or the string 'none'.
        """
        if response is None:
            return False
        if checker is None:
            if 'checker' not in dir( self ):
                if self.responseHasField( 'error', response ):
                    if response[ 'error' ] is None:
                        return False
                    elif response[ 'error' ].upper() == 'NONE':
                        return False
                    elif response[ 'error' ].upper() == 'NULL':
                        return False
                    else:           
                        return True
                else:
                    return False
        if self.checker is None:
            return False
        return checker( response )


#
# :wq
#

