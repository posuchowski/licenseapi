"""
module licenseapi.apis.webclient
"""
import sys, urllib, urllib2

class WebClient( object ):
    """
    Mix-in to let VendorManager subclasses use GET/POST based APIs.
    """
    import httplib

    # request_dict = {}
    # exposed = []

    def __init__( self, url, req, username, password ):
        self.url = url
        self.req = req
        self.append_str = None
        self.username = username
        self.password = password
        self.client = None
        self.phpresponse = False

    def _getClient( self ):
        return self.httplib.HTTPSConnection( self.url )

    def _methodOnlyURL( self, method ):
        if '%' in self.urlbase:
            return self.urlbase % method
        else:
            return None

    def buildURL( self, method ):
        """
        Interpolate method into the URL string, then append
        any self.append_str if not None.
        """
        tmp = self.urlbase + self.urlreq
        if self.append_str is not None:
            tmp += self.append_str
        if '%' in tmp:
            if tmp.count( '%' ) == 3:
                tmp = tmp % ( self.username, self.password, method )
            elif tmp.count( '%' ) == 1:
                tmp = tmp % ( method )
            else:
                raise ValueError(
                    "urlbase + urlreq has %s '%' symbols (unhandled)." % \
                    tmp.count( '%' )
                )
        return tmp

    def setReq( self, req ):
        self.req = req

    def getReq( self ):
        return self.req

    def setAppend( self, append ):
        self.append_str = append

    def getAppend( self ):
        return self.append_str

    def setPhpResponse( self, value=None ):
        if value is None:
            if self.phpresponse is False:
                self.phpresponse = True
            else:
                self.phpresponse = False
        else:
            self.phpresponse = value

    def args_from_content( self, req, valid=None ):
        """
        Set GET string arguments ( &key=value... ) from provided dict.
        """
        append = ""
        for key in req.keys():
                append += "&%s=%s" % ( key, req[ key ] )
        if append == "":
            return False
        self.setAppend( append )
        return True

    def callMethod( self, method ):
        if self.client is None:
            self.client = self._getClient()
        sys.stderr.write( "WebClient GET: %s\n" % self.buildURL( method ) )
        request = self.client.request( 'GET', self.buildURL( method ) )
        text = self.client.getresponse().read()

        if self.phpresponse is True:
            return self.unPHP( text )
        return text

    def unPHP( self, raw ):
        """
        Convert softaculous PHP serialization to Python object.
        """
        from phpserialize import unserialize
        aldente = raw.strip()
        return unserialize( aldente )


class UserAgentSpoofClient( WebClient ):
    """
    Try to cheat the more stingy APIs.
    """
    user_agent = "Mozilla/5.0 (X11; OpenSUSE; Linux x86_64; rv:14.0) " \
                 "Gecko/20100101 Firefox/14.0.1"

    def callMethod( self, method ):
        sys.stderr.write(
            "UserAgentSpoofClient GET: %s\n" % self.buildURL( method )
        )
        request = urllib2.Request( self.buildURL( method ) )
        request.add_header( 'User-Agent', self.user_agent )
        opener = urllib2.build_opener()
        text = opener.open( request ).read()
        if self.phpresponse is True:
            return self.unPHP( text )
        return text
                 

class BasicAuthWebClient( WebClient ):
    """
    Handle basic authentication (e.g. cpanel)
    """
    # urllib2 imported at top

    def __init__( self, *args, **kwargs ):
        """
        Auth handling from example at
        http://docs.python.org/2/library/urllib2.html
        """
        WebClient.__init__( self, *args, **kwargs )
        self.auth_handler = urllib2.HTTPBasicAuthHandler()
        self.auth_handler.add_password(
            realm = "cPanel Licensing System",
            uri = self.auth_url,
            user = self.username,
            passwd = self.password
        )
        self.opener = urllib2.build_opener( self.auth_handler )
        urllib2.install_opener( self.opener )

    def _print_headers( self, method ):
        try:
            urllib2.urlopen( urllib2.Request( self.buildURL( method ) ) )
        except urllib2.HTTPError, e:
            print e.headers
            print e.headers.has_key( 'WWW-Authenticate' )

    def callMethod( self, method ):
        sys.stderr.write(
            "BasicAuthWebClient GET: %s\n" % self.buildURL( method )
        )
        text = urllib2.urlopen(
            urllib2.Request( self.buildURL( method ) )
        ).read()
        return text


class BasicAuthPostClient( BasicAuthWebClient ):
    """
    Adds POST capability to BasicAuthWebClient class.
    Cpanel requires a POST response with some calls to prevent
    "Empty license error".
    """
    def _postEncode( self, post_dict ):
        """
        Change dict into a sequence of tuples and return the
        application/x-www-form-urlencoded form.
        """        
        tseq = [ x for x in post_dict.items() ]
        return urllib.urlencode( tseq )

    def postMethod( self, method, post_dict ):
        sys.stderr.write(
            "BasicAuthPostClient POST: %s => %s\n" % \
                ( str( post_dict ), str( method ) )
        )
        data = self._postEncode( post_dict )
        url  = self._methodOnlyURL( method )
        resp = urllib2.urlopen( urllib2.Request( url, data ) )
        x = resp.read()
        return x


#
# :wq
#        

