'''
Created on 20 Mar 2019

@author: ejimenez-ruiz
'''


class KGEntity(object):
    
    
    def __init__(self, enity_id, label, description, types, source):
        
        self.ident = enity_id
        self.label = label
        self.desc = description #sometimes provides a very concrete type or additional semantics
        self.types = types  #set of semantic types
        self.source = source  #KG of origin: dbpedia, wikidata or google kg
        
    
    def __repr__(self):
        return "<id: %s, label: %s, description: %s, types: %s, source: %s>" % (self.ident, self.label, self.desc, self.types, self.source)

    def __str__(self):
        return "<id: %s, label: %s, description: %s, types: %s, source: %s>" % (self.ident, self.label, self.desc, self.types, self.source)
    
    
    def getId(self):
        return self.ident
    
    def getTypes(self):
        return self.types
    
    def getLabel(self):
        return self.label
    
    def getDescription(self):
        return self.desc
    
    def getSource(self):
        return self.sourcec
    
    