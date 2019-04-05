'''
Created on 19 Mar 2019

@author: ejimenez-ruiz
'''
from SPARQLWrapper import SPARQLWrapper, JSON
from kg.entity import URI_KG
import time


class SPARQLEndpoint(object):
    '''
    classdocs
    '''
    def __init__(self, endpoint_url):
        '''
        Constructor
        '''
        #"http://dbpedia.org/sparql"
        self.sparqlw = SPARQLWrapper(endpoint_url)
        
        self.sparqlw.setReturnFormat(JSON)
        
        
    def getSameEntities(self, ent):
        
        query = self.createSPARQLQuerySameAsEntities(ent)
        
        
        return self.getQueryResultsArityOne(query)
    
    
        
    def getEntitiesForType(self, cls, offset=0, limit=1000):
        
        query = self.createSPARQLEntitiesForClass(cls, offset, limit)
        
        #print(query)
        
        return self.getQueryResultsArityOne(query)
    
        
    def getTypesForEntity(self, entity):
        
        query = self.createSPARQLQueryTypesForSubject(entity)
        
        return self.getQueryResultsArityOne(query)
    

    def getAllTypesForEntity(self, entity):
        
        query = self.createSPARQLQueryAllTypesForSubject(entity)
        
        return self.getQueryResultsArityOne(query)
        

    def getEquivalentClasses(self, uri_class):
        
        query = self.createSPARQLQueryEquivalentClasses(uri_class)
        
        return self.getQueryResultsArityOne(query)
    
    def getAllSuperClasses(self, uri_class):
        
        query = self.createSPARQLQueryAllSuperClassesForSubject(uri_class)
        
        return self.getQueryResultsArityOne(query)
    
    
    
    def getPredicatesForSubject(self, subject_entity, limit=1000):
        
        query = self.createSPARQLQueryPredicatesForSubject(subject_entity, limit)
        
        return self.getQueryResultsArityOne(query)
        
    def getPredicatesForObject(self, obj_entity, limit=1000):
        
        query = self.createSPARQLQueryPredicatesForObject(obj_entity, limit)
        
        return self.getQueryResultsArityOne(query)   
    
    
    
    #Exploits the domain types of the properties
    def getTypesUsingPredicatesForSubject(self, subject_entity, limit=1000):
        
        query = self.createSPARQLQueryDomainTypesOfPredicatesForSubject(subject_entity, limit)
        
        return self.getQueryResultsArityOne(query)
        
    #Exploits the range types of the properties
    def getTypesUsingPredicatesForObject(self, obj_entity, limit=1000):
        
        query = self.createSPARQLQueryRangeTypesOfPredicatesForObject(obj_entity, limit)
        
        return self.getQueryResultsArityOne(query)   
    
    
    
    def getTopTypesUsingPredicatesForSubject(self, subject_entity, limit=5):
        
        query = self.createSPARQLQueryDomainTypesCountOfPredicatesForSubject(subject_entity, limit)
        
        return self.getQueryResultsArityOne(query)
        
    #Exploits the range types of the properties
    def getTopTypesUsingPredicatesForObject(self, obj_entity, limit=5):
        
        query = self.createSPARQLQueryRangeTypesCountOfPredicatesForObject(obj_entity, limit)
        
        return self.getQueryResultsArityOne(query)   
    
    
    
    def getTriplesForSubject(self, subject_entity, limit=1000):
        
        query = self.createSPARQLQueryTriplesForSubject(subject_entity, limit)
        
        return self.getQueryResultsArityTwo(query)
        
    def getTriplesForObject(self, obj_entity, limit=1000):
        
        query = self.createSPARQLQueryTriplesForObject(obj_entity, limit)
        
        return self.getQueryResultsArityTwo(query)    
        
        
        
    
    
    def getQueryResults(self, query, attempts=5):
        
        try:
            
            self.sparqlw.setQuery(query)
            
            return self.sparqlw.query().convert()
        
        except:
            
            print("Query '%s' failed. Attempts: %s" % (query, str(attempts)))
            time.sleep(5) #to avoid limit of calls, sleep 5s
            attempts-=1
            if attempts>0:
                return self.getQueryResults(query, attempts)


    def getQueryResultsArityOne(self, query):
        
        
        results = self.getQueryResults(query, 3)
            
            
        result_set = set()
    
        for result in results["results"]["bindings"]:
            #print(result)
            #print(result["uri"]["value"])
            uri_value = result["uri"]["value"]
            
            if uri_value.startswith(URI_KG.dbpedia_uri) or uri_value.startswith(URI_KG.wikidata_uri) or uri_value.startswith(URI_KG.schema_uri) or uri_value.startswith(URI_KG.dbpedia_uri_resource) or uri_value.startswith(URI_KG.dbpedia_uri_property): 
                result_set.add(uri_value)
        
        
        return result_set
    
    
    
    def getQueryResultsArityTwo(self, query):
        
        #self.sparqlw.setQuery(query)
        #results = self.sparqlw.query().convert()

        results = self.getQueryResults(query, 3)
    
        result_dict = dict()
    
        for result in results["results"]["bindings"]:
            #print(result)
            #print(result["uri"]["value"])
            uria_value = result["uria"]["value"]
            urib_value = result["urib"]["value"]
            
            
            if uria_value.startswith(URI_KG.dbpedia_uri) or uria_value.startswith(URI_KG.wikidata_uri) or uria_value.startswith(URI_KG.schema_uri) or uria_value.startswith(URI_KG.dbpedia_uri_resource) or uria_value.startswith(URI_KG.dbpedia_uri_property): 
                
                    if urib_value.startswith(URI_KG.dbpedia_uri) or urib_value.startswith(URI_KG.wikidata_uri) or urib_value.startswith(URI_KG.schema_uri) or urib_value.startswith(URI_KG.dbpedia_uri_resource) or urib_value.startswith(URI_KG.dbpedia_uri_property):
                        
                        if uria_value not in result_dict:
                            result_dict[uria_value] = set() 
                        
                        result_dict[uria_value].add(urib_value)
                
        
        return result_dict
        

    
    
    


    def createSPARQLQueryTriplesForObject(self, obj, limit=1000):
        return "SELECT DISTINCT ?uria ?urib WHERE { ?uria ?urib <" + obj + "> . } limit " + str(limit)
        
    def createSPARQLQueryTriplesForSubject(self, subject, limit=1000):
        return "SELECT DISTINCT ?uria ?urib WHERE { <" + subject + "> ?uria ?urib . } limit " + str(limit)
    
    
    def createSPARQLQueryPredicatesForSubject(self, subject, limit=1000):
        return "SELECT DISTINCT ?uri WHERE { <" + subject + "> ?uri [] . } limit " + str(limit)
    
    def createSPARQLQueryPredicatesForObject(self, obj, limit=1000):
        return "SELECT DISTINCT ?uri WHERE { [] ?uri <" + obj + "> . } limit " + str(limit)
    
    
    def createSPARQLQueryDomainTypesOfPredicatesForSubject(self, subject, limit=1000):
        return "SELECT DISTINCT ?uri WHERE { <" + subject + "> ?p [] . ?p rdfs:domain ?uri . } limit " + str(limit)
    
    def createSPARQLQueryRangeTypesOfPredicatesForObject(self, obj, limit=1000):
        return "SELECT DISTINCT ?uri WHERE { [] ?p <" + obj + "> . ?p rdfs:range ?uri . } limit " + str(limit)
    
    
    
    #SELECT DISTINCT ?uria COUNT(?uria) as ?urib WHERE { [] ?p <http://dbpedia.org/resource/Scotland> . ?p rdfs:range ?uria . } GROUP BY ?uria ORDER BY DESC(?urib) limit 3
    #SELECT DISTINCT ?uria WHERE { [] ?p <http://dbpedia.org/resource/Scotland> . ?p rdfs:range ?uria . } GROUP BY ?uria ORDER BY DESC(COUNT(?uria)) limit 3
    #SELECT DISTINCT ?uria WHERE { <http://dbpedia.org/resource/Allan_Pinkerton> ?p [] . ?p rdfs:domain ?uria . } GROUP BY ?uria ORDER BY DESC(COUNT(?uria)) limit 3
    #SELECT DISTINCT ?uria COUNT(?uria) as ?urib WHERE { <http://dbpedia.org/resource/Allan_Pinkerton> ?p [] . ?p rdfs:domain ?uria . } GROUP BY ?uria ORDER BY DESC(?urib) limit 3 
    
    def createSPARQLQueryDomainTypesCountOfPredicatesForSubject(self, subject, limit=3):
        return "SELECT DISTINCT ?uri WHERE { <" + subject + "> ?p [] . ?p rdfs:domain ?uri . } GROUP BY ?uri ORDER BY DESC(COUNT(?uri)) limit " + str(limit)
    
    def createSPARQLQueryRangeTypesCountOfPredicatesForObject(self, obj, limit=3):
        return "SELECT DISTINCT ?uri WHERE { [] ?p <" + obj + "> . ?p rdfs:range ?uri . } GROUP BY ?uri ORDER BY DESC(COUNT(?uri)) limit " + str(limit)
    
    

class DBpediaEndpoint(SPARQLEndpoint):
    '''
    classdocs
    
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getEndpoint())
        #"http://dbpedia.org/sparql"
       
       
       
    
        
        
    def getEndpoint(self):
        return "http://dbpedia.org/sparql"



    def getWikiPageRedirect(self, uri_entity):
        
        query = self.createSPARQLQueryWikiPageRedirects(uri_entity)        
        return self.getQueryResultsArityOne(query)
    
    
    
    def createSPARQLEntitiesForClass(self, class_uri, offset=0, limit=1000):
            
            
        return "SELECT DISTINCT ?uri WHERE { ?uri <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <" + class_uri + "> . } ORDER BY RAND() OFFSET " + str(offset) + " limit " + str(limit)
        #return "SELECT DISTINCT ?uri WHERE { ?uri a dbo:Country . } ORDER BY RAND() limit " + str(limit)
    
    
    

    def createSPARQLQueryTypesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri WHERE { <" + uri_subject + "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?uri . }"
    
    
    
    def createSPARQLQueryWikiPageRedirects(self, uri_subject):
            
        return "SELECT DISTINCT ?uri WHERE { <" + uri_subject + "> <http://dbpedia.org/ontology/wikiPageRedirects> ?uri . }"
    
     
        
    def createSPARQLQueryAllTypesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_subject + "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?dt . " \
        + "?dt <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ?uri " \
        + "}" \
        + "UNION {" \
        + "<" + uri_subject + "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?uri . " \
        + "}" \
        + "UNION {" \
        + "<" + uri_subject + "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?dt . " \
        + "?dt <http://www.w3.org/2002/07/owl#equivalentClass> ?uri " \
        + "}" \
        + "}"
        
        
    def createSPARQLQueryEquivalentClasses(self, uri_class):
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_class + "> <http://www.w3.org/2002/07/owl#equivalentClass> ?uri ." \
        + "} " \
        + "UNION " \
        + "{ ?uri <http://www.w3.org/2002/07/owl#equivalentClass> <" + uri_class + "> ." \
        + "} " \
        + "}";
            
        
    def createSPARQLQueryAllSuperClassesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri " \
        + "WHERE { " \
        + "{<" + uri_subject + "> <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ?uri ." \
        + "}" \
        + "UNION {" \
        + "<" + uri_subject + "> <http://www.w3.org/2002/07/owl#equivalentClass> ?uri ." \
        + "}" \
        + "}"
        
    def createSPARQLQuerySameAsEntities(self, uri_entity):
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_entity + "> <http://www.w3.org/2002/07/owl#sameAs> ?uri ." \
        + "} " \
        + "UNION {" \
        + "?uri <http://www.w3.org/2002/07/owl#sameAs> <" + uri_entity + "> ." \
        + "} " \
        + "}";
        

class WikidataEndpoint(SPARQLEndpoint):
    '''
    classdocs
    
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getEndpoint())
        #"http://dbpedia.org/sparql"
   
   
   
    #<http://www.wikidata.org/prop/direct/P31> rdf:type equivalent (instance of)
    #<http://www.wikidata.org/prop/direct/P279> rdfs:subclassof equivalent    
        
        
    def getEndpoint(self):
        return "https://query.wikidata.org/sparql"


    def createSPARQLEntitiesForClass(self, class_uri, offset=0, limit=1000):
            
        #return "SELECT DISTINCT ?uri WHERE { ?uri <http://www.wikidata.org/prop/direct/P31> <" + class_uri + "> . } ORDER BY RAND() limit " + str(limit)
        return "SELECT DISTINCT ?uri WHERE { ?uri <http://www.wikidata.org/prop/direct/P31> <" + class_uri + "> . } ORDER BY RAND() OFFSET " + str(offset) + " limit " + str(limit)
        
    


    def createSPARQLQueryTypesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri WHERE { <" + uri_subject + "> <http://www.wikidata.org/prop/direct/P31> ?uri . }"
    
    
        
        
    def createSPARQLQueryAllTypesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_subject + "> <http://www.wikidata.org/prop/direct/P31> ?dt . " \
        + "?dt <http://www.wikidata.org/prop/direct/P279>* ?uri " \
        + "} " \
        + "UNION {" \
        + "<" + uri_subject + "> <http://www.wikidata.org/prop/direct/P31> ?uri . }" \
        + "}";
        
        
    
    def createSPARQLQueryEquivalentClasses(self, uri_class):
        
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_class + "> <http://www.wikidata.org/prop/direct/P1709> ?uri ." \
        + "} " \
        + "UNION {" \
        + "?uri <http://www.wikidata.org/prop/direct/P2888> <" + uri_class + ">  . " \
        + "} " \
        + "UNION {" \
        + "?uri <http://www.wikidata.org/prop/direct/P1709> <" + uri_class + "> ." \
        + "} " \
        + "UNION {" \
        + "<" + uri_class + "> <http://www.wikidata.org/prop/direct/P2888> ?uri . }" \
        + "}";
        #P1709: equivalent class
        #P2888: exavt match
        
        
        
    ##TODO revise
    def createSPARQLQuerySameAsEntities(self, uri_entity):
        return "SELECT DISTINCT ?uri " \
        + "WHERE {" \
        + "{<" + uri_entity + "> <http://www.wikidata.org/prop/direct/P460> ?uri ." \
        + "} " \
        + "UNION {" \
        + "?uri <http://www.wikidata.org/prop/direct/P460> <" + uri_entity + "> ." \
        + "} " \
        + "}";
        
      
    


if __name__ == '__main__':
    
    '''
    TODO: Filter by schema.org, dbpedia or wikidata
    '''

    ent = "http://dbpedia.org/resource/Scotland"
    ent = "http://dbpedia.org/resource/Allan_Pinkerton"
    #ent = 'http://www.wikidata.org/entity/Q22'

    ep = DBpediaEndpoint()
    types = ep.getAllTypesForEntity("http://dbpedia.org/resource/Scotland")
    #print(len(types), types)
    
    
    
    #predicatesForSubject = ep.getPredicatesForSubject(ent, 10)
    #for p in predicatesForSubject:
    #    print(p)
    
    #predicatesForObject = ep.getPredicatesForObject(ent, 50)
    #for p in predicatesForObject:
    #    print(p)
    
    print("Domain types")
    types_domain = ep.getTopTypesUsingPredicatesForSubject(ent, 3)
    for t in types_domain:
        print(t)
    
    print("Range types")
    types_range = ep.getTopTypesUsingPredicatesForObject(ent, 3)
    for t in types_range:
        print(t)
    
    
    
    cls = "http://dbpedia.org/ontology/Country"
    #cls = "http://dbpedia.org/ontology/Person"
    cls = 'http://www.wikidata.org/entity/Q6256'
    
    
    
    #ep = WikidataEndpoint()
    #types = ep.getAllTypesForEntity("http://www.wikidata.org/entity/Q22")
    #print(len(types), types)
    
    
    
    equiv = ep.getEquivalentClasses(cls)
    #print(len(equiv), equiv)
    
    
    same = ep.getSameEntities(ent)
    #print(len(same), same)
    
    
    
    
    
    
    
        
        
        