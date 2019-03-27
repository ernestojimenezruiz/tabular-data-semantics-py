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



'''
This class aim at providing a lookup access to the KG leading to minimal errors
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
        self.schema_onto = SchemaOrgOntology()
        
        self.dbpedia_ep = DBpediaEndpoint()
        
        
        
        
    def getKGEntities(self, cell, limit=5):
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
        json = dbpedia.getJSONRequest(dbpedia.createParams(query, limit))
        dbpedia_entities = dbpedia.extractKGEntities(json) 
        
        #We complement with types from endpoint and check if they are correct/compatible
        for entity in dbpedia_entities:
            self.__analyseEntityTypes(entity)
        
        
    
        #Find equivalent entities from wikidata (using both wikidata and dbpedia endpoints), 
        #then its types and then try to find conflictive types (it could even be by voting)
        
        
        
        '''
        kg = GoogleKGLookup()
        json = kg.getJSONRequest(kg.createParams(query, limit))
        google_entities = kg.extractKGEntities(json)
         
        wikidata = WikidataAPI()
        json = wikidata.getJSONRequest(wikidata.createParams(query, limit))
        wikidata_entities = wikidata.extractKGEntities(json)
    
        ep = WikidataEndpoint()
        types = ep.getAllTypesForEntity("http://www.wikidata.org/entity/Q22")
        
        '''
        
    def __analyseEntityTypes(self, entity):
        
        print(entity.getId())
        
        print("\t"+str(entity.getTypes(KG.DBpedia)))
        
        
        types_endpoint = self.dbpedia_ep.getAllTypesForEntity(entity.getId())
        
        #print("\t"+str(types))
        
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
        
        
        print("\t"+str(entity.getTypes(KG.DBpedia)))
    
    
    '''
    We check if the source type (endpoint) is among descendants or ancestors of at least one of the target types (lookup)
    '''
    def __checkCompatibilityTypes(self, cls_source, target_types):
        
        for cls_target in target_types:
            if self.__isCompatibleType(cls_source, cls_target):
                return True
            
        
        return False
    
    '''
    We check if the source type is among descendants or ancestors of the target type
    '''
    def __isCompatibleType(self, cls_source, cls_target):
        return False
         
         
         

if __name__ == '__main__':
    
    #query = 'Taylor Swift'
    cell = 'Scotland'
        
    lookup = Lookup()
    
    lookup.getKGEntities(cell, 5)
    
    