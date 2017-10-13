#
# licenseapi.broker
#
import sys, types
from vendor import VendorManagerFactory
from errors import *

class ApiMessage( object ):
    '''
    An ApiMessage is created by RequestBroker and passed to
    the proper function in the VendorManager that answers True
    to _iCanProcessThis( request )
    '''
    import json
    from django.http import HttpResponse

    content_type = 'application/json; charset=utf-8'

    error = "In ApiMessage.%s: %s"

    header_fields = [
        'message_type',
        'response_type',
        'content_length',
        'request'
    ]

    header = {
        'success': {
            'message_type': 'response',
            'response_type': 'success',
            'content_length': 0,
            'content': [],
        },
        'error': {
            'message_type': 'response',
            'response_type': 'error',
            'content_length': 0,
            'content': [],
        },
        'multipart': {
            'message_type': 'response',
            'response_type': 'multipart',
            'content_length': 0,
            'content': [],
        },
    }

    def __init__( self, status=None, content=None, \
                    direction=None, method=None,   \
                    request=None, DEBUG=False      ):

        self.DEBUG = DEBUG
        self.method = method
        self.message = {}
        self.status  = None
        self.requestObj = request
        self.content = []
        self.isMultipart = False

        if status is not None:
            self.setStatus( status )

        if content is not None:
            self.pushContent( content )

    def __len__( self ):
        return len( self.content )

    def __nonzero__( self ):
        return True if len( self ) > 0 else False

    def _debug( self, msg ):
        if self.DEBUG:
            sys.stderr.write( msg + '\n' )
            sys.stderr.flush()

    def _getHeader( self, hname ):
        return self.header[ hname ]

    def _addApiMessage( self, msg ):
        self.setStatus( 'multipart' )
        new = msg.buildMessage()
        if new is not None:
            self.pushContent( new )
        else:
            raise ValueError( self.error %
                ( '_addApiMessage', "Call to msg.getMessage returns None" \
                  ". Content: %s" % str( msg.getContent() )
                )
            )

    def _wrapForMulti( self, item ):
        con = self.header[ 'success' ].copy()
        con[ 'content' ].append( item )
        return con

    def _popContent( self, key, value, item ):
        for part in item[ 'content' ]:
            if key in part:
                if part[ key ] == value:
                    item[ 'content' ].pop( item[ 'content' ].index( part ) )
        return

    @staticmethod
    def newMessage( status=None, content=None ):
        return ApiMessage( status=status, content=content )

    def getRequest( self ):
        return self.requestObj

    def setRequest( self, req ):
        self.requestObj = req

    def findVendor( self ):
        if self.requestObj is None: return ""
        return self.requestObj[ 'content' ][ 0 ][ 'vendor' ]

    def findProduct( self ):
        if self.requestObj is None: return ""
        return self.requestObj[ 'content' ][ 0 ][ 'product' ]
        
    def setStatus( self, status ):
        if self.status == 'multipart': return
        if status not in [ 'multipart', 'success', 'error' ]:
            raise ValueError( self.error %
                ( 'setStatus',
                  "Arg must be in [ 'success', 'error', 'multipart' ]"
                )
            )
        self.status = status

    def setMethod( self, meth ):
        self.method = meth

    def getMethod( self ):
        return self.method

    def getVendor( self ):
        if len( self.content ) == 0: return None
        return self.content[0]['vendor']

    def getContent( self ):
        return self.content

    def pushContent( self, item ):
        if type( item ) in ( dict, list ):
            if self.status == 'multipart' and 'content' not in item:
                # wrap an unwrapped dict in message header if we are multipart
                self.content.append( self._wrapForMulti( item ) )
            else:
                if type( item ) is dict:
                    self.content.append( item )
                else:
                    self.content.extend( item )
            return

        # now assume it's a class type
        # if issubclass( item.__class__, ApiError ) is True:
        if self.status == 'multipart':
            self.pushContent( item.toMessage() )
        else:
            self.setStatus( 'error' )
            self.pushContent( item.toContent() )
        return

        raise ValueError( self.error %
            ( 'pushContent', "Arg must be type 'list', 'dict', or ApiError, " \
              "not %s" % type( item )
            )
        )

    def iterContent( self ):
        for item in self.getContent():
            yield item

    def popMatching( self, key, value ):
        for con in self.content:
            if self.status == 'multipart':
                self._popContent( key, value, con )
            else:
                if key in con:
                    if con[ key ] == value:
                        self.content.pop( self.content.index( con ) )

    def buildMessage( self ):
        if self.status == 'success':
            msg = self.header[ 'success' ]
        elif self.status == 'error':
            msg = self.header[ 'error' ]
        elif self.status == 'multipart':
            msg = self.header[ 'multipart' ]
        else:
            raise ValueError( 'buildMessage',
                "Message status should not be: %s" % self.status
            )

        msg[ 'content' ] = self.getContent()
        msg[ 'content_length' ] = len( self )
        return msg
        
    def toHttp( self ):
        """
        Beware: json.dumps uses lots of memory.
        RLIMIT_AS (total Address Size) has been limited in MethodHandler
        to avoid the OOMKiller. We iterate over the content instead to
        use less ram.
        """
        msg = self.buildMessage()
        jason = self.json.dumps( msg )
        return self.HttpResponse( jason, content_type = self.content_type )

    def toJson( self ):
        return self.json.dumps( self.buildMessage() )


class RequestBroker( object ):
    '''
    Sends request to appropriate Vendor API for processing of individual
    request payloads. Only the request method and content list item
    are sent to each api manager. The results are assembled into a list
    and passed back to the MethodHandler that called RequestBroker.process().
    '''
    api = None
    results = []

    def __init__( self ): pass

    def process( self, jason ):
        """
        This function creates an ApiMessage object and passes its reference to
        the api.processItem() function. The apis can then add content to it.
        One incoming message results in one outgoing ApiMessage.
        """
        msg = ApiMessage( request=jason )
        msg.setMethod( jason[ 'request' ] )
        msg.setStatus( 'success' )  # default

        for item in jason[ 'content' ]:
            if 'vendor' not in item.keys():
                msg.pushContent( MalformedRequestError(
                    hint = 'No vendor provided.'
                    )
                )
                continue
            if msg.getMethod() == 'get_vendor_list':
                return VendorManagerFactory().pushVendorStringList( msg )

            if 'product' not in item.keys():
                msg.pushContent( MalformedRequestError(
                    hint = 'No product provided.'
                    )
                )
                continue
            api = VendorManagerFactory().getVendorManager(
                item[ 'vendor' ]
            )
            r = api.processItem( item, msg )
        return msg


#
# :wq
#

