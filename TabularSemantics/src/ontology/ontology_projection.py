'''
Created on 16 Oct 2020

@author: ernesto
'''

from ontology.onto_access import OntologyAccess
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL
import logging




class OntologyProjection(object):
    '''
    classdocs
    '''


    def __init__(self, urionto, file_projection, classify=False, only_taxonomy=False, bidirectional_taxonomy=False, include_literals=True, avoid_properties=set(), annotation_properties=set(), memory_reasoner='10240'):
        
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        
        #owlready2.reasoning.JAVA_MEMORY='15360'
        
        #Parameters:
        # - If ontology is classified (impact of using HermiT)
        # - Project only_taxonomy (subsumption)
        # - avoid_properties: optional properties to avoid from projection
        # - Annotation properties to consider
        self.urionto = urionto
        self.bidirectional_taxonomy = bidirectional_taxonomy
        self.avoid_properties = avoid_properties
        self.annotation_properties = annotation_properties
        self.include_literals=include_literals
        
        
        ## 1. Create ontology using ontology_access
        self.onto = OntologyAccess(urionto)
        self.onto.loadOntology(classify, memory_reasoner) 
        
        
        ## 2. Initialize RDFlib graph
        self.projection = Graph()
        self.projection.bind("owl", "http://www.w3.org/2002/07/owl#")
        
        #We use special constructors: owl2vec:superClassOf and owl2vec:typeOf 
        if self.bidirectional_taxonomy: 
            self.projection.bind("owl2vec", "http://www.semanticweb.org/owl2vec#")
        
        
        ##(**) No need to over propagate restrictions / over saturate graph. This is left for the random walks.

        
        ## 3. Extract triples for subsumption (optionaly bidirectional: superclass).
        results = self.onto.queryGraph(self.getQueryForAtomicClassSubsumptions())
        for row in results:
            self.addSubsumptionTriple(row[0], row[1])
            
            if self.bidirectional_taxonomy:
                self.addInverseSubsumptionTriple(row[0], row[1])
        
        
        ## 4. Triples for equivalences (split into 2 subsumptions). (no propagation)
        results = self.onto.queryGraph(self.getQueryForAtomicClassEquivalences())
        for row in results:
            self.addSubsumptionTriple(row[0], row[1])
            self.addSubsumptionTriple(row[1], row[0])
            
        
        ## 5. Triples for rdf:type (optional bidirectional: typeOf)
        results = self.onto.queryGraph(self.getQueryForClassTypes())
        for row in results:
            self.addClassTypeTriple(row[0], row[1])
            
            if self.bidirectional_taxonomy:
                self.addInverseClassTypeTriple(row[0], row[1])
        
        
        
        ## 6. Triples for same_as (no propagation)
        results = self.onto.queryGraph(self.getQueryForAtomicIndividualSameAs())
        for row in results:
            self.addSameAsTriple(row[0], row[1])
            self.addSameAsTriple(row[1], row[0])
            
        
        
        
        if (not only_taxonomy):
            
            self.relation_dict={}
            
            for prop in list(self.onto.getObjectProperties()):
                
                print(prop.iri)
                
                ## Filter properties accordingly
                if prop.iri in self.avoid_properties:
                    continue
                
                self.relation_dict.clear()
                
                ## 6. Extract triples for domain and ranges for object properties (object)
                #print(self.getQueryForDomainAndRange(prop.iri))
                results = self.onto.queryGraph(self.getQueryForDomainAndRange(prop.iri))
                self.processPropertyResults(prop.iri, results)
                 
                
                ## 7. Extract triples for restrictions (object)
                ##RHS restrictions (some, all, cardinality) via subclassof 
                results = self.onto.queryGraph(self.getQueryForRestrictionsRHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                ##LHS restrictions (some, all, cardinality) via subclassof    
                results = self.onto.queryGraph(self.getQueryForRestrictionsLHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                

                ## 8. Extract triples for role assertions (object and data)
                results = self.onto.queryGraph(self.getQueryObjectRoleAssertions(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                
                ##EXTRACT BEFORE and propagate on the fly
                ## 9. Extract named inverses and create/propagate new reversed triples. TBOx and ABox
                ## 10. Propagate property equivalences and subsumptions (object and data). TBOx and ABox
                
                
                print(self.relation_dict)
            
            
            #END OBJECT PROPERTIES
            
            
            
            if self.include_literals:
                
                for prop in list(self.onto.getDataProperties()):
                    
                    print(prop.iri)
                    
                    ## Filter properties accordingly
                    if prop.iri in self.avoid_properties:
                        continue
                    
                    
                    self.relation_dict.clear()
                    
                    
                    ## 8. Extract triples for role assertions (data)
                    results = self.onto.queryGraph(self.getQueryDataRoleAssertions(prop.iri))
                    self.processPropertyResults(prop.iri, results)
                         
                    ## 10. Propagate property equivalences and subsumptions (data). TBOx and ABox 
                    
                    print(self.relation_dict)
                    
            
            ##End data properties
            
        
        ##End non taxonomical relationships             
                
                
        
        ##11. Create triples for standard annotations (classes and properties)
        #Read from file + load default ones.
        if self.include_literals:
            pass
        
        
        #Think about classes, annotations (simplified URIs for annotations), axioms, inferred_ancestors classes
        
        
        
        #Save projection graph
        self.projection.serialize(file_projection, format='turtle')
        
    
    def addTriple(self, subject_uri, predicate_uri, object_uri):
        self.projection.add( (subject_uri, predicate_uri, object_uri) )
    
    def processPropertyResults(self, prop_iri, results):
        for row in results:
            self.addTriple(row[0], URIRef(prop_iri), row[1])
            if not row[0] in self.relation_dict:
                self.relation_dict[row[0]]=set()
            self.relation_dict[row[0]].add(row[1])
    
    
    
    
    def addSubsumptionTriple(self, subclass_uri, superclass_uri):
        self.projection.add( (subclass_uri, RDFS.subClassOf, superclass_uri) )
        
        
    def addInverseSubsumptionTriple(self, subclass_uri, superclass_uri):
        self.projection.add( (superclass_uri, URIRef("http://www.semanticweb.org/owl2vec#superClassOf"), subclass_uri) )
    
    
    def addClassTypeTriple(self, indiv_uri, class_uri):
        self.projection.add( (indiv_uri, RDF.type, class_uri) )
    
    
        
    def addInverseClassTypeTriple(self, indiv_uri, class_uri):
        self.projection.add( (class_uri, URIRef("http://www.semanticweb.org/owl2vec#typeOf"), indiv_uri) )
        
        
    def addSameAsTriple(self, indiv_uri1, indiv_uri2):
        self.projection.add( (indiv_uri1, URIRef("http://www.w3.org/2002/07/owl#sameAs"), indiv_uri2) )
    
    
    
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
    
    
    
    def getQueryForAtomicClassEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentClass> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
        }"""
        
    
    
    def getQueryForAtomicObjectPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .  
        }"""
        
        
    def getQueryForAtomicDataPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .  
        }"""
    
    def getQueryForClassTypes(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
        }"""
    
    
        
    def getQueryForAtomicIndividualSameAs(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#sameAs> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .  
        }"""
        
        
    def getQueryObjectRoleAssertions(self, prop_uri):
        
        return """SELECT ?s ?o WHERE {{ ?s <{prop}> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .  
        }}""".format(prop=prop_uri)
    
    
    def getQueryDataRoleAssertions(self, prop_uri):
    
        return """SELECT ?s ?o WHERE {{ ?s <{prop}> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .  
        }}""".format(prop=prop_uri)
            
        
    
        
    def getQueryForDomainAndRange(self, prop_uri):
        
        return """SELECT DISTINCT ?d ?r WHERE {{ <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> ?d . 
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> ?r .
        ?d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        ?r <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        }}""".format(prop=prop_uri)


    #Restrictions on the right hand side
    def getQueryForRestrictionsRHS(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s ?p ?bn .
        ?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> ?o .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> ?o .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> ?o .
        }}
        }}""".format(prop=prop_uri)
        
        
    #Restrictions on the left hand side
    def getQueryForRestrictionsLHS(self, prop_uri):
        
        #Required to include subclassof between ?bn and ?s to avoid redundancy
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?bn <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s . 
        ?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> ?o .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> ?o .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> ?o .
        }}
        }}""".format(prop=prop_uri)


if __name__ == '__main__':
    
    uri_onto = "/home/ernesto/ontologies/test_projection.owl"
    file_projection = "/home/ernesto/ontologies/test_projection_projection.ttl"
    
    projection = OntologyProjection(uri_onto, file_projection, classify=False, only_taxonomy=False, bidirectional_taxonomy=False)
     
    
        
        
        