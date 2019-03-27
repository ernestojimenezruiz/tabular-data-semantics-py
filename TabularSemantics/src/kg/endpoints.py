'''
Created on 19 Mar 2019

@author: ejimenez-ruiz
'''
from SPARQLWrapper import SPARQLWrapper, JSON
from kg.entity import URI_KG


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
        
        
    def getTypesForEntity(self, entity):
        
        query = self.createSPARQLQueryTypesForSubject(entity)
        
        return self.getQueryResultsArityOne(query)
    

    def getAllTypesForEntity(self, entity):
        
        query = self.createSPARQLQueryAllTypesForSubject(entity)
        
        return self.getQueryResultsArityOne(query)
        

    def getEquivalentClasses(self, uri_class):
        
        query = self.createSPARQLQueryEquivalentClasses(uri_class)
        
        return self.getQueryResultsArityOne(query)
        
        


    def getQueryResultsArityOne(self, query):
        
        self.sparqlw.setQuery(query)
        results = self.sparqlw.query().convert()
    
        result_set = set()
    
        for result in results["results"]["bindings"]:
            #print(result["uri"]["value"])
            uri_value = result["uri"]["value"]
            if uri_value.startswith(URI_KG.dbpedia_uri) or uri_value.startswith(URI_KG.wikidata_uri) or uri_value.startswith(URI_KG.schema_uri): 
                result_set.add(uri_value)
        
        
        return result_set
        



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

    def createSPARQLQueryTypesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri WHERE { <" + uri_subject + "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?uri . }"
    
    
        
        
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
        + "{<" + uri_class + "> <http://www.w3.org/2002/07/owl#equivalentClass> ?uri " \
        + "} " \
        + "}";
            
        
    def createSPARQLQueryAllSuperClassesForSubject(self, uri_subject):
            
        return "SELECT DISTINCT ?uri " \
        + "WHERE { " \
        + "{<" + uri_subject + "> <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ?uri " \
        + "}" \
        + "UNION {" \
        + "<" + uri_subject + "> <http://www.w3.org/2002/07/owl#equivalentClass> ?uri " \
        + "}" \
        + "}"
        

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
        + "{<" + uri_class + "> <http://www.wikidata.org/prop/direct/P1709> ?uri " \
        + "} " \
        + "UNION {" \
        + "<" + uri_class + "> <http://www.wikidata.org/prop/direct/P2888> ?uri . }" \
        + "}";
        #P1709: equivalent class
        #P2888: exavt match
        
      
    


if __name__ == '__main__':
    
    '''
    TODO: Filter by schema.org, dbpedia or wikidata
    '''

    ep = DBpediaEndpoint()
    types = ep.getAllTypesForEntity("http://dbpedia.org/resource/Scotland")
    print(len(types), types)
    
    
    ep = WikidataEndpoint()
    types = ep.getAllTypesForEntity("http://www.wikidata.org/entity/Q22")
    print(len(types), types)
    
    
    
    equiv = ep.getEquivalentClasses('http://www.wikidata.org/entity/Q6256')
    print(len(equiv), equiv)
    
    
    
    
    
    
    
        
        
        