import json

class JsonManager:
    def __init__( self, file_path ):
        self.file_path = file_path
        self.load()

    def load( self ):
        try:
            with open( self.file_path ) as f:
                self.data = json.load( f )
        except:
            self.data = {}
            self.save()

    def save( self ):
        with open( self.file_path, 'w' ) as f:
            json.dump( self.data, f, indent=4 )

    def __getitem__( self, key ):
        keys = key.split( '.' )
        d = self.data
        for k in keys:
            d = d[ k ]
        return d

    def __setitem__( self, key, value ):
        keys = key.split( '.' )
        d = self.data
        for k in keys[ : -1 ]:
            if k not in d:
                d[ k ] = {}
            d = d[ k ]
        d[ keys[ -1 ] ] = value
        self.save()
    
    def __delitem__( self, key ):
        parts = key.split('.')
        d = self.data
        for part in parts[:-1]:
            d = d[part]
        del d[parts[-1]]
        self.save()

    def __iter__(self):
        return iter(self.data.items())
