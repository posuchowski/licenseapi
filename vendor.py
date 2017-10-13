#
# licenseapi.vendor
#
import sys, os

class VendorManagerFactory( object ):
    '''
    Factory that returns appropriate API to RequestBroker.
    New API classses should be registered in config.py 
    '''
    import config

    def __init__( self, logger=None ):
        if logger is None:
            self.logger = sys.stderr
        else:
            self.logger = logger

    def pushVendorStringList( self, msg ):
        for k in self.config.APIS.keys():
            if k != 'nullvendor':
                msg.pushContent( { 'vendor': k } )
        return msg
            
    def getVendorManager( self, name ):
        if name not in self.config.APIS.keys():
            raise NotImplementedError(
                "No class name for %s in config.py" % name
            )
        vm = self.config.APIS[ name ]
        cmd = "from apis." + vm + " import " + vm 
        exec( cmd )
        return eval(vm)()

