#
# licenseapi.errors: Error Classes
#

import json
from django.http import HttpResponse

class StopPointReachedException( Exception ):
    '''
    Throw a message into the browser.
    '''
    pass


class ApiError:
    '''
    The parent class of all suberrors.
    '''
    body = {
        'message_type'   : 'response',
        'response_type'  : 'error',
        'content_length' : 1,
        'content'        :
            [
                { 'error_code' : 0,
                  'error_msg'  : "",
                  'error_hint' : ''
                }
            ]
    }

    code = 0
    message = None

    def __init__( self, hint=None ):
        if hint is not None:
            self.body[ 'content' ][0][ 'error_hint' ] = hint 
        self.body[ 'content' ][0][ 'error_code' ] = self.code
        if self.message is None:
            self.body[ 'content' ][0][ 'error_msg' ] = self.__doc__.strip()
        else:
            self.body[ 'content' ][0][ 'error_msg' ] = self.message

    def toMessage( self ):
        return self.body

    def toContent( self ):
        return self.body[ 'content' ]

    def toJson( self ):
        return json.dumps( self.body )

    def toHttp( self ):
        return HttpResponse(
            json.dumps( self.body ),
            content_type = 'text/plain',
            status = 200
        )

class NoError( ApiError ):
    '''
    No error has occurred. This message is an API test message.
    '''
    code = 0

class UnknownError( ApiError ):
    '''
    An unknown error occurred.
    '''
    code = 99

# "Real" errors:

class AlreadyInactiveError( ApiError ):
    '''
    The license is already inactive.
    '''
    code = 11

class AlreadyActiveError( ApiError ):
    '''
    This license is already active.
    '''
    code = 12

class EncodingError( ApiError ):
    '''
    An attempt to parse vendor response failed
    due to incorrect codec or data format.
    '''
    code = 10

class HttpMethodError( ApiError ):
    '''
    An HTTP method other than GET or POST was used to try to access the API.
    '''
    code = 1

class InvalidFieldError( ApiError ):
    """
    Vendor says: invalid value provided for field.
    """
    code = 13

class MalformedRequestError( ApiError ):
    '''
    Malformed Request. JSON string could not be parsed from data provided.
    '''
    code = 2

class NoSuchVendorError( ApiError ):
    '''
    No such vendor.
    '''
    code = 5

class NoSuchProductError( ApiError ):
    '''
    No such product.
    '''
    code = 6

class NoSuchFunctionError( ApiError ):
    '''
    No such function.
    '''
    code = 3

class NoIdentifierProvided( ApiError ):
    '''
    A valid license identifier must be provided.
    If in doubt, check output of get_license_identifier.
    '''
    code = 7

class NoVendorAnalogError( ApiError ):
    '''
    The vendor's API provides no way of processing your request.
    '''
    code = 8

class ShouldNotBeNone( ApiError ):
    '''
    An empty result set was unexpectedly encountered. Something that shouldn't
    be None is None.
    '''
    code = 9

class VendorApiError( ApiError ):
    '''
    Vendor API returns error condition.
    '''
    code = 4


class UnexpectedFallThroughError( ApiError ):
    '''
    A try/except or if/elif/else unexpectedly fell through all choices.
    Please notify a developer.
    '''
    code = 999

class YouShouldNotBeSeeingThisError( ApiError ):
    '''
    Please wait for Gregorian date 2012-12-21. (Mayan date 13.0.0.0.0)
    '''
    code = 666
