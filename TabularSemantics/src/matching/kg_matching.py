'''
Created on 21 Mar 2019

@author: ejimenez-ruiz
'''

from enum import Enum
from kg.entity import KGEntity
from kg.lookup import DBpediaLookup
from kg.lookup import WikidataAPI
from kg.lookup import GoogleKGLookup

from kg.endpoints import DBpediaEndpoint
from kg.endpoints import WikidataEndpoint


class KG(Enum):

        DBpedia = 1

        Wikidata = 2

        Google = 3
        
        All = 4



'''
This class aim at providing a lookup access to the KG leading to minimal errors
'''
class Lookup(object):
    '''
    classdocs
    '''
       
    def __init__(self, KGraph=KG.DBpedia):
        '''
        Constructor
        '''
        #Return types from this knowledge graph
        self.KGraph = KGraph
        
        
        
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
        #One coudl also return the most accurate 5 types combining the 3 KGs... (limit 20 of each of them and then retrieve top-k)
        dbpedia = DBpediaLookup()
        json = dbpedia.getJSONRequest(dbpedia.createParams(query, limit))
        dbpedia_entities = dbpedia.extractKGEntities(json) 
        
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
        
        print("\t"+str(entity.getTypes()))
        
        ep = DBpediaEndpoint()
        types = ep.getAllTypesForEntity(entity.getId())
        
        #print("\t"+str(types))
        
        if len(entity.getTypes())>0:
            for t in types:
                if t not in entity.getTypes():
                    print('\t'+t) 
                    
                    ##Evaluate compatibility with lookup types.
                    ##In same brunch
        
        


if __name__ == '__main__':
    
    #query = 'Taylor Swift'
    cell = 'Scotland'
        
    lookup = Lookup()
    
    lookup.getKGEntities(cell, 5)
    
    