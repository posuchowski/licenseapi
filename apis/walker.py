"""
licenseapi.apis.walker
"""
import xml.etree.ElementTree

class XMLParseError( Exception ):
    """
    Something went wrong with parsing provided XML string.
    """
    pass

class XMLWalker:

    def __init__( self, raw ):
        self.root = xml.etree.ElementTree.fromstring( raw )    
        if self.root is None:
            raise XMLParseError( "Could not parse raw XML: root is None!" )

    def _dump( self ):
        for child in self.root:
            print "%s: %s" % (child.tag, child.text) # child.attrib)

    def getFieldNames( self ):
        """
        Return a list of field names in the response.
        """
        return [ child.tag for child in self.root ]

    def getChild( self, name ):
        return self.root.find( field )

    def getValue( self, field ):
        return self.root.find( field ).text

    def iterTextTuples( self ):
        for child in self.root:
            yield ( child.tag, child.text )

    def toDict( self ):
        new = {}
        for k, v in self.iterTextTuples():
            new[ str(k) ] = str(v)
        return new
        
    
