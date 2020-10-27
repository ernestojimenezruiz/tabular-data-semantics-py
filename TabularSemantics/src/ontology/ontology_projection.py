'''
Created on 16 Oct 2020

@author: ernesto
'''

from ontology.onto_access import OntologyAccess
from rdflib import Graph, URIRef
#, BNode, Literal
from rdflib.namespace import RDF, RDFS
import logging
from constants import annotation_properties
######






class OntologyProjection(object):
    '''
    classdocs
    '''


    def __init__(self, urionto, classify=False, only_taxonomy=False, bidirectional_taxonomy=False, include_literals=True, avoid_properties=set(), additional_annotation_properties=set(), memory_reasoner='10240'):
        
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        
        #owlready2.reasoning.JAVA_MEMORY='15360'
        
        #Parameters:
        # - If ontology is classified (impact of using an OWL 2 Reasoner)
        # - Project only_taxonomy (rdfs:subclassOf and rdf:type)
        # - bidirectional_taxonomy: additional links superclassOf and typeOf
        # - include literals in projection graph: data assertions and annotations
        # - avoid_properties: optional properties to avoid from projection (expected set of (string) URIs, e.g., "http://www.semanticweb.org/myonto#prop1")
        # - Additional annotation properties to consider (in addition to standard annotation properties, e.g. rdfs:label, skos:prefLabel, etc.). Expected a set of (string) URIs, e.g., "http://www.semanticweb.org/myonto#ann_prop1")
        # - Optional memory for the reasoner (10240Mb=10Gb by default)
        
        self.urionto = urionto
                
        self.only_taxonomy = only_taxonomy
        self.bidirectional_taxonomy = bidirectional_taxonomy
        self.include_literals=include_literals
        
        self.avoid_properties = avoid_properties
        self.additional_annotation_properties = additional_annotation_properties
        
        
        
        ## 1. Create ontology using ontology_access
        self.onto = OntologyAccess(urionto)
        self.onto.loadOntology(classify, memory_reasoner)
    
    ##End constructor
    
    
    
    
    ##########################
    #### EXTRACT PROJECTION
    ##########################
    def extractProjection(self):
        
        logging.info("Creating ontology graph projection...")
            
        ## 2. Initialize RDFlib graph
        self.projection = Graph()
        self.projection.bind("owl", "http://www.w3.org/2002/07/owl#")
        self.projection.bind("skos", "http://www.w3.org/2004/02/skos/core#")
        self.projection.bind("obo1", "http://www.geneontology.org/formats/oboInOwl#")
        self.projection.bind("obo2", "http://www.geneontology.org/formats/oboInOWL#")
        
        
        
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
            #print(row[0], row[1])
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
        
        
       
        
        
        if (not self.only_taxonomy):
            
            #We keep a dictionary for the triple subjects (URIref) and objects (URIref) of the active object property
            #This dictionary will be useful to propagate inverses and subproperty relations 
            self.triple_dict={}
            
            for prop in list(self.onto.getObjectProperties()):
                
                #print(prop.iri)
                
                ## Filter properties accordingly
                if prop.iri in self.avoid_properties:
                    continue
                
                self.triple_dict.clear()
                
                ## 7. Extract triples for domain and ranges for object properties (object)
                #print(self.getQueryForDomainAndRange(prop.iri))
                results = self.onto.queryGraph(self.getQueryForDomainAndRange(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                ##7a. Complex domain and ranges
                results_domain = self.onto.queryGraph(self.getQueryForComplexDomain(prop.iri))
                results_range = self.onto.queryGraph(self.getQueryForComplexRange(prop.iri))
                for row_domain in results_domain:
                    for row_range in results_range:
                        self.addTriple(row_domain[0], URIRef(prop.iri), row_range[0])
            
                        if not row_domain[0] in self.triple_dict:
                            self.triple_dict[row_domain[0]]=set()
                        self.triple_dict[row_domain[0]].add(row_range[0])
                
                
                ## 8. Extract triples for restrictions (object)
                ##8.a RHS restrictions (some, all, cardinality) via subclassof and equivalence
                results = self.onto.queryGraph(self.getQueryForRestrictionsRHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                ##8.b Complex restrictions RHS: "R some (A or B)"
                results = self.onto.queryGraph(self.getQueryForComplexRestrictionsRHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                
                ##8.c LHS restrictions (some, all, cardinality) via subclassof (considered above in case of equivalence)
                results = self.onto.queryGraph(self.getQueryForRestrictionsLHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                ##8.d Complex restrictions LHS: "R some (A or B)"
                results = self.onto.queryGraph(self.getQueryForComplexRestrictionsLHS(prop.iri))
                self.processPropertyResults(prop.iri, results)
                

                ## 9. Extract triples for role assertions (object and data)
                results = self.onto.queryGraph(self.getQueryObjectRoleAssertions(prop.iri))
                self.processPropertyResults(prop.iri, results)
                
                
                ## 10. Extract named inverses and create/propagate new reversed triples. TBOx and ABox
                results = self.onto.queryGraph(self.getQueryForInverses(prop.iri))
                for row in results:
                    for sub in self.triple_dict:
                        for obj in self.triple_dict[sub]:
                            self.addTriple(obj, row[0], sub) #Reversed triple. Already all as URIRef
                        
                
                
                ## 11. Propagate property equivalences only (object). TBOx and ABox
                results = self.onto.queryGraph(self.getQueryForAtomicEquivalentObjectProperties(prop.iri))
                for row in results:
                    #print("\t" + row[0])
                    for sub in self.triple_dict:
                        for obj in self.triple_dict[sub]:
                            self.addTriple(sub, row[0], obj) #Inferred triple. Already all as URIRef
                
                
                #print(self.triple_dict)
            
            
            #END OBJECT PROPERTIES
            ######################
            
            
            ##12. Complex but common axioms like
            ## A sub/equiv A and R some B and etc.
            ##Propagate equivalences and inverses
            self.extractTriplesFromComplexAxioms()
            
             
            
            
            #13. LITERAL Triples via Data properties
            if self.include_literals:
                
                for prop in list(self.onto.getDataProperties()):
                    
                    #print(prop.iri)
                    
                    ## Filter properties accordingly
                    if prop.iri in self.avoid_properties:
                        continue
                    
                    
                    self.triple_dict.clear()
                    
                    
                    ## 13a. Extract triples for role assertions (data)
                    results = self.onto.queryGraph(self.getQueryDataRoleAssertions(prop.iri))
                    self.processPropertyResults(prop.iri, results)
                         
                    
                    ## 13b. Propagate property equivalences only (data). ABox
                    results = self.onto.queryGraph(self.getQueryForAtomicEquivalentDataProperties(prop.iri))
                    for row in results:
                        #print("\t" + row[0])
                        for sub in self.triple_dict:
                            for obj in self.triple_dict[sub]:
                                self.addTriple(sub, row[0], obj) #Inferred triple. Already all as URIRef
                        
                    
                    
                    #print(self.triple_dict)
                    
            
            ##End DATA properties
            ######################
            
        
        ##End non TAXONOMICAL relationships             
        ######################
        
        
        
        ##14. Create triples for standard annotations (classes and properties)
        #Additional given annotation properties + default ones defined in annotation_properties
        if self.include_literals:
            
            #We add default annotation properties from constants.annotation_properties
            self.additional_annotation_properties.update(annotation_properties.values)
            
            for ann_prop_uri in self.additional_annotation_properties:
                #print(ann_prop_uri)
                
                results = self.onto.queryGraph(self.getQueryForAnnotations(ann_prop_uri))
                for row in results:
                    #Filter by language
                    try:
                        #Keep labels in English or not specified
                        if row[1].language=="en" or row[1].language==None:
                            self.addTriple(row[0], URIRef(ann_prop_uri), row[1])
                            #print(row[1].language)
                    except AttributeError:
                        pass
        
        #End optional literal additions        
        
        logging.info("Projection created into a Graph object (RDFlib library)")
        
        
    ##END PROJECTOR
    ######################
    
    
    
    
    
    ##Returns an rdflib Graph object
    def getProjectionGraph(self):    
        return self.projection
    
    ##Serialises the projection into a file (turtle format) 
    def saveProjectionGraph(self, file_projection):
    
        #Saves projection
        self.projection.serialize(file_projection, format='turtle')
        logging.info("Projection saved into turtle file: " + file_projection)
    
    
    
    def addTriple(self, subject_uri, predicate_uri, object_uri):
        self.projection.add( (subject_uri, predicate_uri, object_uri) )
    
    
    #Adds triples to graphs and updates property dictionary
    def processPropertyResults(self, prop_iri, results):
        for row in results:
            self.addTriple(row[0], URIRef(prop_iri), row[1])
            
            if not row[0] in self.triple_dict:
                self.triple_dict[row[0]]=set()
            self.triple_dict[row[0]].add(row[1])
    
    
    
    
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
    
    
    
    
    def extractTriplesFromComplexAxioms(self):
        #Using sparql it is harder to get this type of axioms
        #Axioms involving intersection with unions.
        #e.g. A equiv B and R some D    
        for cls in self.onto.getClasses():
            
            expressions = set()
            expressions.update(cls.is_a, cls.equivalent_to)
                                    
            for cls_exp in expressions:
                try:          
                    ##cls_exp is of the  form A and (R some B) and ... as it contains attribute "get_is_a"
                    ##Typically composed by atomic concepts and restrictions
                    for cls_exp2 in cls_exp.Classes:  ##also accessible with .Classes
                        try:
                            #print(cls_exp2)
                            #Case of atomic class
                            self.addSubsumptionTriple(URIRef(cls.iri), URIRef(cls_exp2.iri))
                            
                            if self.bidirectional_taxonomy:
                                self.addInverseSubsumptionTriple(URIRef(cls.iri), URIRef(cls_exp2.iri))
                                
                        except AttributeError:
                            try:
                                #Case of restrictions with object property
                                if (not self.only_taxonomy) and (not cls_exp2.property.iri in self.avoid_properties):
                                    
                                    targets = set()
                                    
                                    #UnionOf or IntersectionOf atomic classes
                                    if hasattr(cls_exp2.value, "Classes"):
                                        for target_cls in cls_exp2.value.Classes:
                                            if hasattr(target_cls, "iri"):
                                                targets.add(target_cls.iri)
                                        
                                    #Atomic tragte class
                                    elif hasattr(cls_exp2.value, "iri"):
                                        targets.add(cls_exp2.value.iri)
                                        
                                    for target_cls in targets:
                                        
                                        self.addTriple(URIRef(cls.iri), URIRef(cls_exp2.property.iri), URIRef(target_cls))
                                            
                                        ##Propagate equivalences and inverses for cls_exp2.property
                                        ## 12a. Extract named inverses and create/propagate new reversed triples.
                                        results = self.onto.queryGraph(self.getQueryForInverses(cls_exp2.property.iri))
                                        for row in results:
                                            self.addTriple(URIRef(target_cls), row[0], URIRef(cls.iri)) #Reversed triple. Already all as URIRef
                            
                                        ## 12b. Propagate property equivalences only (object).
                                        results = self.onto.queryGraph(self.getQueryForAtomicEquivalentObjectProperties(cls_exp2.property.iri))
                                        for row in results:
                                            self.addTriple(URIRef(cls.iri), row[0], URIRef(target_cls)) #Inferred triple. Already all as URIRef
                                    ##end targets
                                    
                            except AttributeError:
                                pass  # Not atomic nor supported restriction
                            
                except AttributeError:
                    pass ##No right expressions
                
            
        
    
    
    
    #isIRI,isBlank,isLiteral, isNumeric.
    
    def getQueryForAtomicClassSubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
        FILTER (isIRI(?s) && isIRI(?o))
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
        FILTER (isIRI(?s) && isIRI(?o)) 
        }"""
        
    
    
    def getQueryForAtomicObjectPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .  
        }"""
        
    def getQueryForAtomicEquivalentObjectProperties(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{ 
        ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .
        {{
        ?p <http://www.w3.org/2002/07/owl#equivalentProperty> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#equivalentProperty> ?p .
        }} 
        }}""".format(prop=prop_uri)
        
        
    def getQueryForAtomicDataPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .  
        }"""
        
    def getQueryForAtomicEquivalentDataProperties(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{ 
        ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .
        {{
        ?p <http://www.w3.org/2002/07/owl#equivalentProperty> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#equivalentProperty> ?p .
        }} 
        }}""".format(prop=prop_uri)
        
    
    
    def getQueryForClassTypes(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
        FILTER (isIRI(?s) && isIRI(?o))
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
            
        
    
    def getQueryForComplexDomain(self, prop_uri):
        return """SELECT DISTINCT ?d where {{
        {{
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?d ] ] ] .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?d ] ] ] .
        }}
        filter( isIRI( ?d ) )
        }}""".format(prop=prop_uri)
    
    
    def getQueryForComplexRange(self, prop_uri):
        return """SELECT DISTINCT ?r where {{
        {{
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?r ] ] ] .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?r ] ] ] .
        }}
        filter( isIRI( ?r ) )
        }}""".format(prop=prop_uri)
    
    
        
    def getQueryForDomainAndRange(self, prop_uri):
        
        return """SELECT DISTINCT ?d ?r WHERE {{ <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> ?d . 
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> ?r .
        FILTER (isIRI(?d) && isIRI(?r))
        }}""".format(prop=prop_uri)
        #?d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        #?r <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .



    def getQueryForInverses(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{ 
        ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .
        {{
        ?p <http://www.w3.org/2002/07/owl#inverseOf> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#inverseOf> ?p .
        }} 
        }}""".format(prop=prop_uri)
        
        
        

    #Restrictions on the right hand side: A sub/equiv R some A. ?p is sub or equiv
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
        FILTER (isIRI(?s) && isIRI(?o))        
        }}""".format(prop=prop_uri)
        #
        
    #Restrictions on the left hand side:  R some A sub A
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
        FILTER (isIRI(?s) && isIRI(?o))
        }}""".format(prop=prop_uri)
        #
    
    
        #Restrictions on the right hand side: A sub/equiv R some (C or D)
    def getQueryForComplexRestrictionsRHS(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s ?p ?bn .
        ?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        FILTER (isIRI(?s) && isIRI(?o))        
        }}""".format(prop=prop_uri)
        #
        
    #Restrictions on the left hand side: R some (C or D) sub A
    def getQueryForComplexRestrictionsLHS(self, prop_uri):
        
        #Required to include subclassof between ?bn and ?s to avoid redundancy
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?bn <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s . 
        ?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> [ <http://www.w3.org/2002/07/owl#intersectionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#someValuesFrom> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#allValuesFrom> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        UNION
        {{
        ?bn <http://www.w3.org/2002/07/owl#onClass> [ <http://www.w3.org/2002/07/owl#unionOf> [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#rest>* [ <http://www.w3.org/1999/02/22-rdf-syntax-ns#first> ?o ] ] ] .
        }}
        FILTER (isIRI(?s) && isIRI(?o))
        }}""".format(prop=prop_uri)
        #    
        
    

    def getQueryForAnnotations(self, ann_prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{
        ?s <{ann_prop}> ?o .  
        }}""".format(ann_prop=ann_prop_uri)
        
        
    
    
    #todo_include_todos    
    #14. Think about classes, annotations (simplified URIs for annotations), axioms, inferred_ancestors classes
    #get support to create structures list of classes, and store them as necessary. OWL2Vec reads them as strings, check that
        
    
    
    
    
        

if __name__ == '__main__':
    
    uri_onto = "/home/ernesto/ontologies/test_projection.owl"
    file_projection = "/home/ernesto/ontologies/test_projection_projection.ttl"
    
    projection = OntologyProjection(uri_onto, classify=True, only_taxonomy=False, bidirectional_taxonomy=True, include_literals=True)
    projection.extractProjection()
    #projection.getProjectionGraph()  gets RDFLib's Graph object with projection
    projection.saveProjectionGraph(file_projection)
    
    
    #projection.extractTriplesFromComplexAxioms() 
    
        
        
        