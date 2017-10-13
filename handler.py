#
# licenseapi.handler
#

import sys, json, types, resource, pprint

import errors

from broker      import RequestBroker
from django.http import HttpResponse
from errors      import ApiError, MalformedRequestError

class MethodHandler( object ):
    '''
    This is the JSON handler for the licenseapi application.
    '''
    def __init__( self ):
        self._set_resource_limits()
        self.broker = RequestBroker()

    def _set_resource_limits( self ):
        """
        Try not to take the system down with us...
        """
        # resource.setrlimit( resource.RLIMIT_STACK, ( 1024, 2048 ) )
        resource.setrlimit( resource.RLIMIT_AS, ( 1024000000L, 2048000000L ) )

    def _validate( self, request ):
        if request.method == 'POST':
            try:
                data = request.POST[ 'data' ]
            except:
                try:
                    # for PHP json_encode
                    data = request.POST.dict().keys()[0]
                except:
                    return errors.MalformedRequestError(
                        hint = "Where's your POST data?"
                    )
        elif request.method == 'GET':
            try:
                data = request.GET[ 'data' ]
            except:
                return MalformedRequestError(
                    hint = "Where's your GET data?"
                )
        else:
            return HttpMethodError()

        try:
            j = json.loads( data )
            z = j[ 'message_type'   ]  # Assert that these fields are in the
            z = j[ 'request'        ]  # request. It's not sufficient to simply
            z = j[ 'content_length' ]  # use an expression without an lvalue --
            z = j[ 'content'        ]  # compiler probably optimizes it out. 
        except:
            return errors.MalformedRequestError(
                hint = "Missing fields in json data object"
            )

        if type( j['content'] ) != list:
            return errors.MalformedRequestError(
                hint = "'content' field must be an array type"
            )
        if j == {}:
            return errors.MalformedRequestError(
                hint = "Request object parses empty"
            )

        return j

    def pong( self ):
        '''
        Returns response to 'ping' request, response_type = 'pong'.
        '''
        return HttpResponse(
            json.dumps( {
                'message_type'   : 'reponse',
                'response_type'  : 'pong',
                'content_length' : 0,
                'content'        : []
            } )
        )

    def incoming( self, request ):
        '''
        Process our JSON request, which should come in in the 'data' attribute,
        either of GET or POST.
        '''
        jason = self._validate( request )
        if isinstance( jason, errors.ApiError ) is True:
            return jason.toHttp()

        # the only one we process here
        if jason[ 'request' ] == 'ping':
            return self.pong()

        sys.stderr.write( "Request Broker: passing on json object: %s\n" \
            % str( jason )
        ) #DEBUG
        result = self.broker.process( jason )
        return result.toHttp()

