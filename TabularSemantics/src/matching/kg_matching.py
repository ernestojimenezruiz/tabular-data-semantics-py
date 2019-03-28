'''
Created on 21 Mar 2019

@author: ejimenez-ruiz
'''

from kg.entity import KGEntity
from kg.lookup import DBpediaLookup
from kg.lookup import WikidataAPI
from kg.lookup import GoogleKGLookup

from kg.endpoints import DBpediaEndpoint
from kg.endpoints import WikidataEndpoint

from ontology.onto_access import DBpediaOntology
from ontology.onto_access import SchemaOrgOntology

from kg.entity import KG
from kg.entity import URI_KG

from util.utilities import is_empty




'''
This class aim at providing a lookup access to the KG leading to minimal errors
It will also optionally combine. No only one KG but several 
'''
class Lookup(object):
    '''
    classdocs
    '''
       
    def __init__(self): #KGraph=KG.DBpedia
        '''
        Constructor
        '''
        #Return types from this knowledge graph
        #self.KGraph = KGraph
        
        self.dbpedia_onto = DBpediaOntology()
        self.dbpedia_onto.loadOntology(True)
        self.schema_onto = SchemaOrgOntology()
        self.schema_onto.loadOntology(True)
        
        self.dbpedia_ep = DBpediaEndpoint()
        
    
    
    def getTypesForEntity(self, uri_entity, kg=KG.DBpedia):
        
        if kg==KG.DBpedia:
            
            label=uri_entity
            if uri_entity.startswith(URI_KG.dbpedia_uri_resource):
                label=uri_entity.replace(URI_KG.dbpedia_uri_resource, '')
            
            ##we call our method to get look-up types for the URI. Only SPARQL endpoint types may contain errors
            entities = self.getKGEntities(label, 10, uri_entity) 
            
            
            ##In case not match in look up
            if is_empty(entities):
                #We retrieve from SPRQL endpoint
                return self.dbpedia_ep.getAllTypesForEntity(uri_entity)
                
            else:
                ##only one element
                for entity in entities:
                    return entity.getTypes(kg)
            
                
        #TBC
        elif kg==KG.Wikidata:
            pass
        elif kg==KG.Google:    
            pass
        
        return set()
    
        
        
    def getKGEntities(self, cell, limit=5, filter=''):
        '''
        Given the text of a cell extracts entity objects.
        Note that an entity contains an id, a label, a description, a set of types from dbpedia, wikidata and schema.org,
        and the source (dbpedia, wikidata or google)
        '''
        
        #Strategy:
        #0. Incremental repair: start with sth simple
        #1. Identify cases where dbpedia lookup and endpoint do not agree
        #2. We have dbpedia (may require a fix...) and schema.org taxonomies to identify conflicting branches
        #3. Use alignment to identify same entities and have more evidence about types
        #3a. Lexical
        #3b. Based on embeddings
        #4. If not provided mapping among classes (there seem to be available mappings), we may use alignment as well (lexical and embedding)
            
        query = cell

        #Get KG entities from DBpedia, Wikidata and KG
        #One could also return the most accurate 5 types combining the 3 KGs... (limit 20 of each of them and then retrieve top-k)
        dbpedia = DBpediaLookup()
        dbpedia_entities = dbpedia.getKGEntities(query, limit, filter)
        
        
        #We complement with types from endpoint and check if they are correct/compatible
        for entity in dbpedia_entities:
            self.__analyseEntityTypes(entity)
        
        
        
        
        return dbpedia_entities
    
    
        #Next steps
        #Find equivalent entities from wikidata (using both wikidata and dbpedia endpoints), 
        #then its types and then try to find conflictive types (it could even be by voting)
        
        '''
        kg = GoogleKGLookup()
         
        wikidata = WikidataAPI()
        
       
        '''
        
    def __analyseEntityTypes(self, entity):
        
        #print(entity.getId())
        
        #print("\t"+str(entity.getTypes(KG.DBpedia)))
        
        #Filter by type?
        types_endpoint = self.dbpedia_ep.getAllTypesForEntity(entity.getId())
        
        #print("\t"+str(types_endpoint))
        
        if len(entity.getTypes())>0:
            
            for t in types_endpoint:
                
                if t not in entity.getTypes():
                    
                    ##Evaluate compatibility with lookup types.
                    ##In same brunch
                    ##We use DBpedia for now
                    if self.__checkCompatibilityTypes(t, entity.getTypes(KG.DBpedia)):
                        entity.addType(t) 
                    
        else: #No types from lookup
            entity.addTypes(types_endpoint)
        
        
        #print("\t"+str(entity.getTypes(KG.DBpedia)))
    
    
    '''
    We check if the source type (endpoint) is among descendants or ancestors of at least one of the target types (lookup)
    '''
    def __checkCompatibilityTypes(self, cls_source_uri, target_types):
        
        for cls_target_uri in target_types:
            if self.__isCompatibleType(cls_source_uri, cls_target_uri):
                return True
            
        
        return False
    
    '''
    We check if the source type is among descendants or ancestors of the target type
    '''
    def __isCompatibleType(self, cls_source_uri, cls_target_uri):
        
        
        cls_source = self.dbpedia_onto.getClassByURI(cls_source_uri)
        cls_target = self.dbpedia_onto.getClassByURI(cls_target_uri)
        
        ##TODO  We rely on DBpedia only for now
        if cls_source==None or cls_target==None:
            return False
        
        ancestors = self.dbpedia_onto.getAncestorsURIs(cls_target)
        descendants = self.dbpedia_onto.getDescendantURIs(cls_target)
        
        if cls_source_uri in ancestors or cls_source_uri in descendants:
            return True
        
        return False
         
         
         

if __name__ == '__main__':
    
    #query = 'Taylor Swift'
    cell = 'Scotland'
        
    lookup = Lookup()
    
    #lookup.getKGEntities(cell, 5)
    types = lookup.getTypesForEntity('http://dbpedia.org/resource/Wales')
    
    for t in types:
        print(t)
    