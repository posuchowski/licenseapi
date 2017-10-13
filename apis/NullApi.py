import sys, codecs, pprint

from manager import VendorManager

class NullApi( VendorManager ):
    '''
    In the interest of implementing the shortest front-to-back case.
    Well, front to middle in this case.
    '''
    
    vendor = 'nullvendor'
    products = [ 'nullproduct', 'nullerproduct', 'mostnullproduct' ]

    field_dict = {}; request_dict = {}; response_dict = {}
    res_field_dict = req_field_dict = None

    exposed = [
        'get_support_list',
        'get_license_identifier',
        'get_license_list',
    ]

    def get_support_list( self, ignored, msg ):
        results = []
        for p in self.products:
            msg.pushContent(
                { 'vendor' : self.vendor,
                  'product': p
                }
            )
        return results

    def get_license_identifier( self, ignored, msg ):
        msg.pushContent(
            { 'vendor': self.vendor,
              'product': 'nullproduct',
              'identifier': 'nullidentifier',
              'value': 'Anything you want'
            }
        )

    def get_license_list( self, ignored, msg ):
        msg.pushContent(
            { 'vendor': self.vendor,
              'product': self.products[0],
              'ipaddr': '10.0.0.1',
              'serial': 'ABCD-BCDE-CDEF-DEFG',
              'license_id': '1',
            }
        )

        
