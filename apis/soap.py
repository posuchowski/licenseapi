#
# module apis.soap
#

class SudsClient( object ):
    '''
    Mixin some Suds. Apparently SOAPy is all washed up.
    '''
    from suds.client import Client
    from suds.xsd.doctor import Import, ImportDoctor

    def __init__( self, wsdl_url, imports=None, username=None, password=None, ):
        self.wsdl_url = wsdl_url

        if imports:
            imp = self.Import( imports[ 0 ], location=imports[ 1 ] )
            imp.filter.add( 'https://netenberg.com/api' )
            doctor = self.ImportDoctor( imp )
            self.client = \
                self.Client( wsdl_url,
                    doctor=doctor,
                    plugins=[ self.ImportDoctor( imp ) ]
                )
        else:
            self.client = self.Client( wsdl_url )
        self.soap = self.client.service

    def _examine( self ):
        print self.client

    def setSoapPort( self, port ):
        self.client.set_options( port = port )


#
# :wq
#

