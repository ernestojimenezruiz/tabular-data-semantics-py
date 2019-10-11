'''
Created on 21 Mar 2019

@author: ejimenez-ruiz
'''

import time

from kg.endpoints import DBpediaEndpoint
from kg.endpoints import WikidataEndpoint
from kg.entity import KG
from kg.entity import KGEntity
from kg.entity import URI_KG
from kg.lookup import DBpediaLookup
from kg.lookup import GoogleKGLookup
from kg.lookup import WikidataAPI
from ontology.onto_access import DBpediaOntology
from ontology.onto_access import SchemaOrgOntology
from util.utilities import *


class Endpoint(object):
    '''
    This class aim at identifying errors in DBpedia ENDPOINT when retrieving samples for training
    Positive/negative samples for candidate classes 
    '''
    
    '''
    def queryTripleByClass(top_k, c):
    triples = list()
    s = sparql.Service(SPARQL_END_POINT, "utf-8", "GET")
    statement = 'select distinct str(?s), str(?p), str(?o), str(?l) where {?s ?p ?o. ?o rdf:type <%s>. ' \
                '?o rdfs:label ?l. FILTER( langMatches(lang(?l), "en"))} ORDER BY RAND() limit %d' % (c, top_k)
    result = s.query(statement)
    for row in result.fetchone():
        triples.append([row[0], row[1], row[2], row[3]])
    return triples
    '''

    
    
    
    def __init__(self): 
        '''
        Constructor
        '''
        
        self.dbpedia_ep = DBpediaEndpoint()
        self.wikidata_ep = WikidataEndpoint()
        
        self.lookup = Lookup()
        
        
        
    def __analyseEntityPredicateStrategy(self, ent, cls_uri):
        '''
        Analyses correctness of cls_uri as type of ent using Predicate types strategy
        '''
        
        predicate_types = self.lookup.__getTypesPredicateStrategy(ent)
        
        if len(predicate_types)==0:
            return None
        
        if cls_uri in predicate_types:
            return True
        
        return False
    
    
    def __analyseEntityLooukStrategy(self, ent, cls_uri):
        '''
        Analyses correctness of cls_uri as type of ent using Look-up types
        '''
        
        #Note that if not look-up types, then we return the sparql types as they are
        ##IF lookup types, the sparql types must be compatible 
        clean_lookup_types = self.lookup.getTypesForEntity(ent, KG.DBpedia)
        
        if len(clean_lookup_types)==0:
            return None
        
        if cls_uri in clean_lookup_types:
            return True
        
        return False
    
        
        
    def __analyseEntityWikidataStrategy(self, ent, cls_uri, wikidata_classes):
        '''
        Analyses correcteness of cls_uri as type of ent using wikidata
        '''
        
        #b. Get equivalent wikidata entity (if any)
        same_entities = self.dbpedia_ep.getSameEntities(ent)
                 
        wikidata_entities = getFilteredResources(same_entities, KG.Wikidata) ##typically one entity
        
        
        ##If no equivalent entities we then go for the lookup strategy
        if len(wikidata_entities)==0:
            return self.__analyseEntityLooukStrategy(ent, cls_uri)
        
        
        #print(wikidata_entities)
        for wk_ent in wikidata_entities:                    
            #c. Check if wikidata type from (a) is within types of equivalent entity from (b)
                          
            #print("\t"+wk_ent)      
            wk_ent_types = self.wikidata_ep.getAllTypesForEntity(wk_ent)  #we consider supertypes to extend compatibility
            time.sleep(0.01) #to avoid limit of calls
                    
            intersect = wk_ent_types.intersection(wikidata_classes)
                    
            if len(intersect)>0:
                return True
            
        
        return False
        
    
    
    def getEntitiesForDBPediaClass(self, cls_uri, limit=1000):
        '''
        It currently expects a URL from DBpedia
        '''   
        
        ##We query a subset of entities for sampling
        clean_db_entities = dict()
        
        offset=0
        
        #To guarantee the required number of (clean) entities for the class
        while len(clean_db_entities) < limit:
            
            #db_entities = self.dbpedia_ep.getEntitiesForType(cls_uri, offset*limit*5, limit*5) #We extract more than required as many of them will be noisy
            db_entities = self.dbpedia_ep.getEntitiesLabelsForType(cls_uri, offset*limit*5, limit*5)
            #print("Entities",len(db_entities))
            
            #For wikidata strategy
            #a. Get equivalent class from wikidata (if any)
            db_eq_cls = self.dbpedia_ep.getEquivalentClasses(cls_uri)
            wikidata_classes = getFilteredTypes(db_eq_cls, KG.Wikidata) ##typically one class
            
            filtered_look_up=0
            filtered_wikidata=0
            filtered_predicates=0
            
            for ent in db_entities:
                if len(clean_db_entities)>=limit:
                    print("%d, %d, %d, %d" %(len(clean_db_entities), filtered_look_up, filtered_predicates, filtered_wikidata))
                    return clean_db_entities 
                
                results_look_up = self.__analyseEntityLooukStrategy(ent, cls_uri)
                
                if results_look_up==None:
                    
                    results_predicates = self.__analyseEntityPredicateStrategy(ent, cls_uri)
                    
                    if results_predicates==None:
                        
                        if self.__analyseEntityWikidataStrategy(ent, cls_uri, wikidata_classes): #wikidata strategy (it is very costly)
                            clean_db_entities[ent] = db_entities[ent]
                        else:
                            filtered_wikidata+=1
                            #print ("Entity filtered by wikidata", ent)
                         
                    elif results_predicates: #passed predicates strategy
                        clean_db_entities[ent] = db_entities[ent]
                    else:
                            #print ("Entity filtered by predicates", ent)
                            filtered_predicates+=1
                
                elif results_look_up: #passed look-up strategy
                    clean_db_entities[ent] = db_entities[ent]
                else:
                    #print ("Entity filtered by look-up", ent)
                    filtered_look_up+=1
                
                
            
            
            #OLD STRATEGY: too slow
            #if (len(wikidata_classes)==0): ## No wikidata class then look-up strategy
            #    for ent in db_entities:
            #        if len(clean_db_entities)>=limit:
            #            return clean_db_entities 
            #        if self.__analyseEntityLooukStrategy(ent, cls_uri):
            #            clean_db_entities.add(ent)
            #else:
            #    for ent in db_entities:
            #        if len(clean_db_entities)>=limit:
            #            return clean_db_entities
            #        if self.__analyseEntityWikidataStrategy(ent, cls_uri, wikidata_classes):
            #            clean_db_entities.add(ent)
                       
                
                
            #print(len(clean_db_entities))
            offset+=1
            
            #Limit of iterations
            if offset>5:
                print("%d, %d, %d, %d" %(len(clean_db_entities), filtered_look_up, filtered_predicates, filtered_wikidata))
                return clean_db_entities
        
            
        print("%d, %d, %d, %d" %(len(clean_db_entities), filtered_look_up, filtered_predicates, filtered_wikidata))
        return clean_db_entities
        
        
        
        #Strategy 3:
        #Query wikidata if there is equivalent class, then return sameAS dbpedia entities for the wikidata entities
        
        
        
        #Strategy 4: 
        #Combine dbpedia and wikidata results
        
        
        
       
        
        



class Lookup(object):
    '''    
    This class aim at providing a lookup access to the KG leading to minimal errors
    It will also optionally combine. No only one KG but several 
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
        self.wikidata_ep = WikidataEndpoint()
        
    
    
    def getTypesForEntity(self, uri_entity, kg=KG.DBpedia):
        
        #print("QUERY",uri_entity)
        
        if kg==KG.DBpedia:
            types=set() 
            types_redirects = set()
            
            #Original entity
            types.update(self.getTypesForDBPediaEntity(uri_entity))
                       
            #Redirects if any
            #See dbo:wikiPageRedirects -> similar to same_as inside dbpedia
            redirects = self.dbpedia_ep.getWikiPageRedirect(uri_entity)
            
            for uri_redirect in redirects: #Typically only one
                types_redirects.update(self.getTypesForDBPediaEntity(uri_redirect))
                
            
            if len(types)==0: #We use the ones of the redirects
                types.update(types_redirects)
            else: #types of redirects can be dirty
                for t in types_redirects:
                    if self.__checkCompatibilityTypes(t, types):
                        types.add(t)    
            
            
            #Commented because it was slow for a large dataset
            #if is_empty(types) or (len(types)==1 and "Agent" in list(types)[0]):
            #    #Wikidata strategy to complement if empty endpoint and look-up or only type "Agent"
            #    print(types)
            #    types.update(self.__getTypesWikidataStrategy(uri_entity))
            #    print(types)
            
            
            return types
                
        #TBC
        elif kg==KG.Wikidata:
            pass
        elif kg==KG.Google:    
            pass
        
        return set()
    
    
    
    def __getTypesLookupStrategy(self, uri_entity):
        
        kg=KG.DBpedia
        
        label=uri_entity
        if uri_entity.startswith(URI_KG.dbpedia_uri_resource):
                label=uri_entity.replace(URI_KG.dbpedia_uri_resource, '')
            
        ##we call our method to get look-up types for the URI. Only SPARQL endpoint types may contain errors
        #It also includes wikidata strategy inside
        entities = self.getKGEntities(label, 10, uri_entity) #fulter by uri_entity
            
            
        ##In case not match in look up
        if is_empty(entities):
            
            types=set()
            
            #Dbpedia Enpoint strategy 
            types_endpoint = getFilteredTypes(self.dbpedia_ep.getAllTypesForEntity(uri_entity), KG.DBpedia)
        
            #Predicates strategy (uses top types)
            types_domain_range = self.__getTypesPredicateStrategy(uri_entity)
            
            if len(types_domain_range)>0:
            
                #They can be noisy, so do not add them yet
                #types.update(types_domain_range)
                
                ##Check compatibility of types_endpoint
                for t in types_endpoint:
                    
                    if t not in types_domain_range:
                        if self.__checkCompatibilityTypes(t, types_domain_range):
                            types.add(t)
                            
                #If no compatible types we just use the ones coming from domain/ranges
                if len(types)>0:
                    types.update(types_domain_range)
            
            #If still empty we use 
            if len(types)==0:
                #We add endpoint types
                types.update(types_endpoint)
        
            
            return types
        
            
                
        else:
            ##shoudl be only one element from lookup
            for entity in entities:
                return entity.getTypes(kg)
            
            
    def __getTypesPredicateStrategy(self, uri_entity):
        '''
        Exploits the domain and range types of the predicates in triples with uri_entity as subject or object
        '''
        
        types = set()
        
        #Top-2
        types.update(getFilteredTypes(self.dbpedia_ep.getTopTypesUsingPredicatesForObject(uri_entity, 2), KG.DBpedia))
        
        #We use top one here, as there less properties associated to an entity. And We only need one wrong to be in the top-k
        
        #Top-1
        #Error-prone as many properties are not properly used
        #Only uses if current range types are compatible
        types_domain = getFilteredTypes(self.dbpedia_ep.getTopTypesUsingPredicatesForSubject(uri_entity, 1), KG.DBpedia)
        
        #if len(types)==0:
        #    types.update(types_domain)
        #else:
        if len(types)>0:
            for t in types_domain:
                if self.__checkCompatibilityTypes(t, types):
                    types.add(t)
            
            
        
        #TODO: Alternative Strategies: use intersection of types_range and types_domain in non empty. May increase recall (remove min input/output edges in queries) and precision
        #If empty then use as now. 
        
        
        
        return types
        
        
    
    
    def __getTypesWikidataStrategy(self, uri_entity):
        
        print("\tUsing wikidata strategy for " + uri_entity)
        
        #Gets equivalent wikidata entities
        same_entities = self.dbpedia_ep.getSameEntities(uri_entity)
        wikidata_entities = getFilteredResources(same_entities, KG.Wikidata) ##typically one entity
        
        wk_ent_types = set()
        dp_types = set()
        dp_types_all = set()
           
        if len(wikidata_entities)==0:
            return wk_ent_types
        
        for wk_ent in wikidata_entities:                    
            
            #print("WK ent: "+wk_ent)
            
            #Get types for wikidata entities      
            wk_ent_types.update(self.wikidata_ep.getAllTypesForEntity(wk_ent))  #we consider all supertypes to extend compatibility
            
            
            #Problematic concept
            #Wikimedia disambiguation page
            if URI_KG.wikimedia_disambiguation_concept in wk_ent_types:
                wk_ent_types.clear()
            
            #Check if: wk_ent_types
            
            
            
          
        for t in wk_ent_types:    
            #print("WK cls: " +t)
            #Get equivalent dbpedia types        
            #print(self.wikidata_ep.getEquivalentClasses(t))    
            dp_types.update(getFilteredTypes(self.wikidata_ep.getEquivalentClasses(t), KG.DBpedia))
            
        
        #get superclasses
        for t in dp_types:    
            #print("DBp type: " +t)
            dp_types_all.update(self.dbpedia_ep.getAllSuperClasses(t))
        
        
        return getFilteredTypes(dp_types_all, KG.DBpedia)
        
        
        
    
    
    def getTypesForDBPediaEntity(self, uri_entity):
        
        #types=set()
        
        #Types from DBpedia Endpoint may be dirty. So we use 2 strategies: wikidata and lookup types
        #TODO: check compatibility among strategies?
        
        #Look-up strategy  also includes wikidata strategy
        types = self.__getTypesLookupStrategy(uri_entity)
        
        
        #print("Main", types) 
        return types
        
        
        
       
        
        
        
        
            
            
        ##Additional strategy...
        #Check equivalent entity from wikidata, get classes from wikidata, get equivalent in dbpedia enpoint
        
        
    
        
        
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
        types_endpoint = getFilteredTypes(self.dbpedia_ep.getAllTypesForEntity(entity.getId()), KG.DBpedia)
        
        #print("\t"+str(types_endpoint))
        
        if len(entity.getTypes())>0:
            
            for t in types_endpoint:
                
                if t not in entity.getTypes():
                    
                    ##Evaluate compatibility with lookup types.
                    ##In same branch
                    ##We use DBpedia for now
                    if self.__checkCompatibilityTypes(t, entity.getTypes(KG.DBpedia)):
                        entity.addType(t) 
                    
        else: #No types from lookup
            
            #We use wikidata strategy
            #Not great for compatibility as we need to better explore the returned types
            #types_wk_strategy = self.__getTypesWikidataStrategy(entity.getId())
            
            
            #We use range-domain-predicate strategy (uses top-types)
            types_domain_range = self.__getTypesPredicateStrategy(entity.getId())
            
            
            if len(types_domain_range)>0:
            
                #They can be noisy, so do not add them yet
                #entity.addTypes(types_domain_range)
                
                ##Check compatibility of types_endpoint
                for t in types_endpoint:
                    
                    if t not in types_domain_range:
                        if self.__checkCompatibilityTypes(t, types_domain_range):
                            entity.addType(t)
                
                #DANGEROUS, as domain and range types contain amny errors
                #If no compatible type we just use the ones coming from domain/ranges
                #if len(entity.getTypes())>0:
                #    entity.addTypes(types_domain_range)
            
            #If still empty we use endpoint
            if len(entity.getTypes())==0:
                #We add endpoint types
                entity.addTypes(types_endpoint)
            
            
            ##Last resource if not types
            if len(entity.getTypes())>0:
                entity.addTypes(types_domain_range)
            
            #We complement with wikidata strategy
            #entity.addTypes(types_wk_strategy)
            

            
        
        
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
    
    
    cls = "http://dbpedia.org/ontology/Country"
    #cls = "http://dbpedia.org/ontology/Person"
    
    
    ep = Endpoint()
    

    # seconds passed since epoch
    init = time.time()
    
    entities=set()
    #entities = ep.getEntitiesForDBPediaClass(cls, 50)
    print("Extracted entities: ", len(entities))
    for ent in entities:
        print(ent)
    
    end = time.time()
    

    #local_time = time.ctime(seconds)
    print("Time:", end-init)
    
    
    #query = 'Taylor Swift'
    #cell = 'Scotland'
    
    
    lookup = Lookup()
    
    # seconds passed since epoch
    init = time.time()
    #lookup.getKGEntities(cell, 5)
    types = lookup.getTypesForEntity('http://dbpedia.org/resource/Wales')
    
    end = time.time()
        #local_time = time.ctime(seconds)
    print("Time:", end-init)
    
    for t in types:
        print(t)
    