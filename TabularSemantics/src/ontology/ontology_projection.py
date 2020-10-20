'''
Created on 16 Oct 2020

@author: ernesto
'''

from ontology.onto_access import OntologyAccess
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL



class OntologyProjection(object):
    '''
    classdocs
    '''


    def __init__(self, urionto, file_projection, classify=False, only_taxonomy=False, bidirectional_taxonomy=False, avoid_properties=set(), memory_reasoner='10240'):
        
        #owlready2.reasoning.JAVA_MEMORY='15360'
        
        #Parameters:
        # - If ontology is classified (impact of using HermiT)
        # - Project only_taxonomy (subsumption)
        # - avoid_properties: optional properties to avoid from projection
        # - Annotation properties to consider
        self.urionto = urionto
        self.bidirectional_taxonomy = bidirectional_taxonomy
        self.avoid_properties = avoid_properties
        
        
        ## 1. Create ontology using ontology_access
        self.onto = OntologyAccess(urionto)
        self.onto.loadOntology(classify, memory_reasoner) 
        
        
        ## 2. Initialize RDFlib graph
        self.projection = Graph()
        
        
        ##(**) No need to over propagate restrictions / over saturate graph. This is left for the random walks.

        
        ## 3. Extract triples for subsumption (optionaly bidirectional: superclass).
        results = self.onto.queryGraph(self.getQueryForAtomicClassSubsumptions())
        for row in results:
            self.addTaxonomyTriple(row[0], row[1])
        
        
        
        
        
        ## 4. Triples for equivalences (split into 2 subsumptions). (no propagartion)
        ## 5. Triples for rdf:type (optional bidirectal: typeOf)
        ## 6. Triples for same_as (no propagation)
        
        if (not only_taxonomy):
            pass
            ## Filter properties accordingly
            ## 6. Extract triples for restrictions (object)
            ## 7. Extract triples for domain and ranges for object properties (object)
            ## 8. Extract triples for role assertions (object and data)
            ## 9. Extract named inverses and create/propagate new reversed triples. TBOx and ABox
            ## 10. Propagate property equivalences and subsumptions (object and data). TBOx and ABox
            
        
        
        
        ##10. Create triples for standard annotations (classes and properties)
                
        
        #Think about classes, annotations (simplified URIs for annotations), axioms, inferred_ancestors classes
        
        
        
        #Save projection graph
        self.projection.serialize(file_projection, format='turtle')
        
        
        
    def addTaxonomyTriple(self, subclass_uri, superclass_uri):
        self.projection.add( (subclass_uri, RDFS.subClassOf, superclass_uri) )
    
    
    
    def getQueryForAtomicClassSubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
        }"""
        
    def getQueryForAtomicObjectPropertySubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subPropertyOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .  
        }"""
        
        
    def getQueryForAtomicDataPropertySubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subPropertyOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .  
        }"""
    




if __name__ == '__main__':
    
    uri_onto = "/home/ernesto/ontologies/test_projection.owl"
    file_projection = "/home/ernesto/ontologies/test_projection_projection.ttl"
    
    projection = OntologyProjection(uri_onto, file_projection, classify=True)
     
    
        
        
        