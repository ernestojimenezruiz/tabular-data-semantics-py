'''
Created on 16 Oct 2020

@author: ernesto
'''


from ontology.onto_access import OntologyAccess, Reasoner
from rdflib import Graph, URIRef
#, BNode, Literal
from rdflib.namespace import RDF, RDFS
import logging
from constants import annotation_properties
import time
from docutils.nodes import row
######






class OntologyProjection(object):
    '''
    classdocs
    '''


    def __init__(self, urionto, reasoner=Reasoner.NONE, only_taxonomy=False, bidirectional_taxonomy=False, include_literals=True, avoid_properties=set(), additional_annotation_properties=set(), memory_reasoner='10240'):
        
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
        
        self.propagate_domain_range = (reasoner==Reasoner.STRUCTURAL)
        
        
        ## 1. Create ontology using ontology_access
        self.onto = OntologyAccess(urionto)
        self.onto.loadOntology(reasoner, memory_reasoner)
    
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
        logging.info("\tExtracting subsumption triples")
        start_time = time.time()
        results = self.onto.queryGraph(self.getQueryForAtomicClassSubsumptions())
        for row in results:
            
            self.addSubsumptionTriple(row[0], row[1])
            
            if self.bidirectional_taxonomy:
                self.addInverseSubsumptionTriple(row[0], row[1])
                
        logging.info("\t\tTime extracting subsumption: %s seconds " % (time.time() - start_time))
        
        ## 4. Triples for equivalences (split into 2 subsumptions). (no propagation)
        logging.info("\tExtracting equivalence triples")
        start_time = time.time()
        results = self.onto.queryGraph(self.getQueryForAtomicClassEquivalences())
        for row in results:
            #print(row[0], row[1])
            self.addSubsumptionTriple(row[0], row[1])
            self.addSubsumptionTriple(row[1], row[0])
            
        logging.info("\t\tTime extracting equivalences: %s seconds " % (time.time() - start_time))
        
        
        '''
        THIS CODE IS one order of magnitude SLOWER as it goes instance by instance
        start_time = time.time()
        logging.info("\tExtracting class membership and sameAs triples")        
        
        for indiv in list(self.onto.getIndividuals()):
            
            ## 5. Triples for rdf:type (optional bidirectional: typeOf)
            #start_time2 = time.time()            
            results = self.onto.queryGraph(self.getQueryForIndividualClassTypes(indiv.iri))               
            for row in results:
                self.addClassTypeTriple(URIRef(indiv.iri), row[0])
                
                if self.bidirectional_taxonomy:
                    self.addInverseClassTypeTriple(URIRef(indiv.iri), row[0])
            #logging.info("\t\tTime extracting class membership: %s seconds " % (time.time() - start_time2))
            
            ## 6. Triples for same_as (no propagation)
            #start_time2 = time.time()            
            results = self.onto.queryGraph(self.getQueryForIndividualSameAs(indiv.iri))
            for row in results:
                self.addSameAsTriple(URIRef(indiv.iri), row[0])
                self.addSameAsTriple(row[0], URIRef(indiv.iri))
            #logging.info("\t\tTime and sameAs: %s seconds " % (time.time() - start_time2))
        
        logging.info("\t\tTime extracting class membership and sameAs: %s seconds " % (time.time() - start_time))
        '''
        
        
        ## 5. Triples for rdf:type (optional bidirectional: typeOf)
        start_time = time.time()
        logging.info("\tExtracting class membership triples.")                
        results = self.onto.queryGraph(self.getQueryForAllClassTypes())               
        for row in results:
            self.addClassTypeTriple(row[0], row[1])
           
            if self.bidirectional_taxonomy:
                self.addInverseClassTypeTriple(row[0], row[1])
                 
        logging.info("\t\tTime extracting class membership: %s seconds " % (time.time() - start_time))
        
        
        ## 6. Triples for same_as (no propagation)        
        logging.info("\tExtracting sameAs triples")
        start_time = time.time()
        results = self.onto.queryGraph(self.getQueryForAllSameAs())
        for row in results:
            self.addSameAsTriple(row[0], row[1])
            self.addSameAsTriple(row[1], row[0])
            
        logging.info("\t\tTime extracting sameAs: %s seconds " % (time.time() - start_time))
        
       
        
        #We check if only taxonomy when adding the triple. We want to check the use of properties to propagate domains and ranges (not well treated by HermiT and slow with Pellet) 
        #if (not self.only_taxonomy):
            
        #We keep a dictionary for the triple subjects (URIref) and objects (URIref) of the active object property
        #This dictionary will be useful to propagate inverses and subproperty relations 
        self.triple_dict={}
        
        
        ##To propagate ranges and domains
        #1. To use in first iterations
        self.domains=set()
        self.ranges=set()
        #2. To use in complex restriction method
        self.domains_dict={}
        self.ranges_dict={}
            
            
        ####################
        #OBJECT PROPERTIES
        for prop in list(self.onto.getObjectProperties()):
            
            ## Filter properties accordingly
            if prop.iri in self.avoid_properties:
                continue
            
            
            start_time = time.time()
            logging.info("\tExtracting triples associated to " + str(prop.name))
            #print(prop.iri)
            
            
            
            self.domains_dict[prop.iri]=set()
            self.ranges_dict[prop.iri]=set()
            
            
                
            self.triple_dict.clear()
            ##We keep domains and ranges to propagate the inference in case the reasoner fails or HermiT is used (it misses many inferences)
            ##Useful to infer subsumptions and class types
            self.domains.clear()
            self.ranges.clear()
                
            ## 7. Extract triples for domain and ranges for object properties (object)
            #print(self.getQueryForDomainAndRange(prop.iri))
            #logging.info("\t\tExtracting domain and range for " + str(prop.name))
            results = self.onto.queryGraph(self.getQueryForDomainAndRange(prop.iri))
            self.processPropertyResults(prop.iri, results, True, True)
            
            #To propagate domain/range entailment. Only atomic domains
            results_domain = self.onto.queryGraph(self.getQueryForDomain(prop.iri))
            results_range = self.onto.queryGraph(self.getQueryForRange(prop.iri))
            for row_domain in results_domain:
                self.domains.add(row_domain[0])
                self.domains_dict[prop.iri].add(row_domain[0])
                
            for row_range in results_range:
                self.ranges.add(row_range[0])
                self.ranges_dict[prop.iri].add(row_range[0])
            
                
            ##7a. Complex domain and ranges
            #logging.info("\t\tExtracting complex domain and range for " + str(prop.name))
            results_domain = self.onto.queryGraph(self.getQueryForComplexDomain(prop.iri))
            results_range = self.onto.queryGraph(self.getQueryForComplexRange(prop.iri))
            #for row_range in results_range:
            #    self.ranges.add(row_range[0])         
            for row_domain in results_domain:
                #self.domains.add(row_domain[0])         
                for row_range in results_range:
                    
                    self.addTriple(row_domain[0], URIRef(prop.iri), row_range[0])
            
                    if not row_domain[0] in self.triple_dict:
                        self.triple_dict[row_domain[0]]=set()
                    self.triple_dict[row_domain[0]].add(row_range[0])
                
            
            
            ## 8. Extract triples for restrictions (object)
            ##8.a RHS restrictions (some, all, cardinality) via subclassof and equivalence
            #logging.info("\t\tExtracting RHS restrictions for " + str(prop.name))
            results = self.onto.queryGraph(self.getQueryForRestrictionsRHSSubClassOf(prop.iri))
            self.processPropertyResults(prop.iri, results, True, True)
            results = self.onto.queryGraph(self.getQueryForRestrictionsRHSEquivalent(prop.iri))
            self.processPropertyResults(prop.iri, results, True, True)
                
            ##Not optimal to query via SPARQL: integrated in complex axioms method
            ##8.b Complex restrictions RHS: "R some (A or B)"
            #logging.info("\t\tExtracting complex RHS restrictions for " + str(prop.name))
            #results = self.onto.queryGraph(self.getQueryForComplexRestrictionsRHSSubClassOf(prop.iri))
            #self.processPropertyResults(prop.iri, results)
            ##results = self.onto.queryGraph(self.getQueryForComplexRestrictionsRHSEquivalent(prop.iri))
            ##self.processPropertyResults(prop.iri, results)
                
                
            ##8.c LHS restrictions (some, all, cardinality) via subclassof (considered above in case of equivalence)
            #logging.info("\t\tExtracting LHS restrictions for " + str(prop.name))
            results = self.onto.queryGraph(self.getQueryForRestrictionsLHS(prop.iri))
            self.processPropertyResults(prop.iri, results, True, True)
                
            ##8.d Complex restrictions LHS: "R some (A or B)"
            #logging.info("\t\tExtracting Complex LHS restrictions for " + str(prop.name))
            results = self.onto.queryGraph(self.getQueryForComplexRestrictionsLHS(prop.iri))
            self.processPropertyResults(prop.iri, results, True, True)
                

            ## 9. Extract triples for role assertions (object and data)
            #logging.info("\t\tExtracting triples for role assertions for " + str(prop.name))
            results = self.onto.queryGraph(self.getQueryObjectRoleAssertions(prop.iri))
            self.processPropertyResults(prop.iri, results, False, True)
                
            
            
            if (not self.only_taxonomy):    
                ## 10. Extract named inverses and create/propagate new reversed triples. TBOx and ABox
                #logging.info("\t\tExtracting inverses for " + str(prop.name))
                results = self.onto.queryGraph(self.getQueryForInverses(prop.iri))
                for row in results:
                    for sub in self.triple_dict:
                        for obj in self.triple_dict[sub]:
                            self.addTriple(obj, row[0], sub) #Reversed triple. Already all as URIRef
                            
                    
                    
                ## 11. Propagate property equivalences only (object). TBOx and ABox
                #logging.info("\t\tExtracting equivalences for " + str(prop.name))
                results = self.onto.queryGraph(self.getQueryForAtomicEquivalentObjectProperties(prop.iri))
                for row in results:
                    #print("\t" + row[0])
                    for sub in self.triple_dict:
                        for obj in self.triple_dict[sub]:
                            self.addTriple(sub, row[0], obj) #Inferred triple. Already all as URIRef
                    
            
            #print(self.triple_dict)
            logging.info("\t\tTime extracting triples for property: %s seconds " % (time.time() - start_time))
            
            
        #END OBJECT PROPERTIES
        ######################
        
        
        
             
            
            
            
                
        start_time = time.time()
        logging.info("\tExtracting data property assertions")
        ####################
        ##DATA PROPERTIES
        for prop in list(self.onto.getDataProperties()):
                    
            #print(prop.iri)
                    
            ## Filter properties accordingly
            if prop.iri in self.avoid_properties:
                continue
            
            
            self.domains_dict[prop.iri]=set()
                    
                
            self.triple_dict.clear()
            self.domains.clear()
            self.ranges.clear()
                
            #12. LITERAL Triples via Data properties            
            #if self.include_literals:
             
            ## 12a. Domain
            results_domain = self.onto.queryGraph(self.getQueryForDomain(prop.iri))            
            for row_domain in results_domain:
                self.domains.add(row_domain[0])
                self.domains_dict[prop.iri].add(row_domain[0])
            
            
            ## 12b. Restrictions
            results = self.onto.queryGraph(self.getQueryForDataRestrictionsRHSSubClassOf(prop.iri))
            self.processPropertyResults(prop.iri, results, True, False)  ##Propagates domain and range but avoids adding the triple
            results = self.onto.queryGraph(self.getQueryForDataRestrictionsRHSEquivalent(prop.iri))
            self.processPropertyResults(prop.iri, results, True, False)
            
                
            ## 12c. Extract triples for role assertions (data)
            results = self.onto.queryGraph(self.getQueryDataRoleAssertions(prop.iri))
            self.processPropertyResults(prop.iri, results, False, self.include_literals)
                                       
                    
            ## 12d. Propagate property equivalences only (data). ABox
            results = self.onto.queryGraph(self.getQueryForAtomicEquivalentDataProperties(prop.iri))
            for row in results:
                #print("\t" + row[0])
                for sub in self.triple_dict:
                    for obj in self.triple_dict[sub]:
                        self.addTriple(sub, row[0], obj) #Inferred triple. Already all as URIRef
                        
                    
                    
            #print(self.triple_dict)
                    
        logging.info("\t\tTime extracting data property assertions: %s seconds " % (time.time() - start_time))
                    
            
        ##End DATA properties
        ######################
        
        
        
        ######################################
        ##13. Complex but common axioms like (involving both object and data properties)
        ##1. A sub/equiv A and R some B and etc.
        ##2. A sub/equiv R some (B or D)
        ##Propagate equivalences and inverses
        start_time = time.time()
        logging.info("\tExtracting complex equivalence axioms")
        self.extractTriplesFromComplexAxioms()
        logging.info("\t\tTime extracting complex equivalence axioms: %s seconds " % (time.time() - start_time))
        ######################################
        
              
        
        ##ANNOTATIONS
        ##14. Create triples for standard annotations (classes and properties)
        #Additional given annotation properties + default ones defined in annotation_properties
        if self.include_literals:
            
            start_time = time.time()
            logging.info("\tExtracting annotations.")
            
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
            
            
            logging.info("\t\tTime extracting annotations: %s seconds " % (time.time() - start_time))
            
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
    def processPropertyResults(self, prop_iri, results, are_tbox_results, add_triple):
        
        for row in results:
            
            if (not self.only_taxonomy) & add_triple:
                
                self.addTriple(row[0], URIRef(prop_iri), row[1])
                
                if not row[0] in self.triple_dict:
                    self.triple_dict[row[0]]=set()
                self.triple_dict[row[0]].add(row[1])
            
        
            ##Approximate reasoning propagation domain and ranges
            if self.propagate_domain_range:
                
                if are_tbox_results:
                    
                    self.propagateDomainTbox(row[0])
                    try:
                        self.propagateRangeTbox(row[1])
                    except: ##case of dataproperty restrictions
                        pass
                
                else:
                    self.propagateDomainAbox(row[0])
                    try:
                        self.propagateRangeAbox(row[1])
                    except: ##case of dataproperty restrictions
                        pass
    
    
    
    
    def propagateDomainTbox(self, source):
        for domain_cls in self.domains:
            self.addSubsumptionTriple(source, domain_cls)
            if self.bidirectional_taxonomy:
                self.addInverseSubsumptionTriple(source, domain_cls)
    
    
    def propagateRangeTbox(self, target):
    
        #Ranges will be empty for the data properties
        for range_cls in self.ranges:
            self.addSubsumptionTriple(target, range_cls)
            if self.bidirectional_taxonomy:
                self.addInverseSubsumptionTriple(target, range_cls)
                            
            
    
    def propagateDomainAbox(self, source):
        
        for domain_cls in self.domains:
            self.addClassTypeTriple(source, domain_cls)
            if self.bidirectional_taxonomy:
                self.addInverseClassTypeTriple(source, domain_cls)
    
    def propagateRangeAbox(self, target):              
                    
        for range_cls in self.ranges:
            self.addClassTypeTriple(target, range_cls)
            if self.bidirectional_taxonomy:
                self.addInverseClassTypeTriple(target, range_cls)
                            
        
    
    
    
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
        #Axioms involving intersection and unions.
        #e.g. A sub/equiv B and/or R some D
        ##e.g. A sub/equiv R some (D and/or E)    
        
        for cls in self.onto.getClasses():
            
            expressions = set()
            expressions.update(cls.is_a, cls.equivalent_to)
                                    
            for cls_exp in expressions:
                
                try:          
                    ##cls_exp is of the  form A and (R some B) and ... as it contains attribute "get_is_a or Classes"
                    ##Typically composed by atomic concepts and restrictions                    
                    for cls_exp2 in cls_exp.Classes:  ##Accessing the list in Classes 
                        try:
                            #print(cls_exp2)
                            #Case of atomic class in union or intersection
                            self.addSubsumptionTriple(URIRef(cls.iri), URIRef(cls_exp2.iri))
                            
                            if self.bidirectional_taxonomy:
                                self.addInverseSubsumptionTriple(URIRef(cls.iri), URIRef(cls_exp2.iri))
                                
                        except AttributeError:
                            try:
                                if (not self.only_taxonomy) and (not cls_exp2.property.iri in self.avoid_properties):
                                
                                    #Case of restrictions in union/intersection
                                    ##------------------------------------------
                                    self.extractTriplesForRestriction(cls, cls_exp2)
                                    
                            except AttributeError:
                                pass  # Not supported restriction
                    
                except AttributeError:
                    
                    #Case of restrictions with special focus on the case with union/intersection in target                    
                    ##------------------------------------------
                    try:
                        if (not self.only_taxonomy) and (not cls_exp.property.iri in self.avoid_properties):
                            self.extractTriplesForRestriction(cls, cls_exp) 
                    
                    except AttributeError:
                        pass  # Not supported restriction 
                
            
        
    
    
    def extractTriplesForRestriction(self, cls, cls_exp_rest):
        
        try:
                                    
            targets = set()
            
            property_iri = cls_exp_rest.property.iri
            
            ##TODO Propagate domain for both data properties and object properties
            for domain_cls in self.domains_dict[property_iri]:
                self.addSubsumptionTriple(URIRef(cls.iri), domain_cls)
                if self.bidirectional_taxonomy:
                    self.addInverseSubsumptionTriple(URIRef(cls.iri), domain_cls)
            
            
            
                                    
            #UnionOf or IntersectionOf atomic classes in target of restriction
            if hasattr(cls_exp_rest.value, "Classes"):
                for target_cls in cls_exp_rest.value.Classes:
                    if hasattr(target_cls, "iri"):  ##other expressions ignored
                        targets.add(target_cls.iri)
                                        
            #Atomic target class in target of restrictions
            elif hasattr(cls_exp_rest.value, "iri"):
                
                target_cls_iri = cls_exp_rest.value.iri
                
                targets.add(target_cls_iri)
                
                #TODO Propagate range only in this case
                for range_cls in self.ranges_dict[property_iri]:
                    self.addSubsumptionTriple(URIRef(target_cls_iri), range_cls)
                    if self.bidirectional_taxonomy:
                        self.addInverseSubsumptionTriple(URIRef(target_cls_iri), range_cls)
                                    
                                        
            for target_cls in targets:
                                        
                self.addTriple(URIRef(cls.iri), URIRef(property_iri), URIRef(target_cls))
                                            
                ##Propagate equivalences and inverses for cls_exp2.property
                ## 12a. Extract named inverses and create/propagate new reversed triples.
                results = self.onto.queryGraph(self.getQueryForInverses(property_iri))
                for row in results:
                    self.addTriple(URIRef(target_cls), row[0], URIRef(cls.iri)) #Reversed triple. Already all as URIRef
                            
                ## 12b. Propagate property equivalences only (object).
                results = self.onto.queryGraph(self.getQueryForAtomicEquivalentObjectProperties(property_iri))
                for row in results:
                    self.addTriple(URIRef(cls.iri), row[0], URIRef(target_cls)) #Inferred triple. Already all as URIRef
            ##end targets
                                    
        except AttributeError:
            pass  # Not supported restriction 
        
    
    
    
    
    #isIRI,isBlank,isLiteral, isNumeric.
    
    def getQueryForAtomicClassSubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .          
        FILTER (isIRI(?s) && isIRI(?o) 
        && str(?o) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Thing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Thing'
        )
        }"""
    #This makes query slower for large taxonomies:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .    
    
        
    def getQueryForAtomicClassSubsumptionsRHS(self, cls_iri):
        
        return """SELECT ?o WHERE {{ <{cls}> <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .
        FILTER (isIRI(?o)
        && str(?o) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Thing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Thing'
        )
        }}""".format(cls=cls_iri)
    
    
    def getQueryForAtomicObjectPropertySubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subPropertyOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .  
        }"""
    #type in query is required as rdfs:subPropertyOf is used by both data propertes and object properties
        
    def getQueryForAtomicDataPropertySubsumptions(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subPropertyOf> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .  
        }"""
    #type in query is required as rdfs:subPropertyOf is used by both data propertes and object properties
    
    
    def getQueryForAtomicClassEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentClass> ?o .  
        FILTER (isIRI(?s) && isIRI(?o)
        && str(?o) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Nothing'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Thing'
        && str(?s) != 'http://www.w3.org/2002/07/owl#Thing'
        ) 
        }"""
    #This makes query slower for large taxonomies:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .    
    
    
    def getQueryForAtomicObjectPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty> .  
        }"""
    #type in query is required as owl:equivalentProperty is used by both data propertes and object properties
      
    def getQueryForAtomicEquivalentObjectProperties(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{        
        {{
        ?p <http://www.w3.org/2002/07/owl#equivalentProperty> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#equivalentProperty> ?p .
        }}
        FILTER (isIRI(?p)) 
        }}""".format(prop=prop_uri)
    #Union is required in this case   
        
        
    def getQueryForAtomicDataPropertyEquivalences(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#equivalentProperty> ?o .
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> . 
        ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty> .  
        }"""
    #type in query is required as owl:equivalentProperty is used by both data propertes and object properties
        
    def getQueryForAtomicEquivalentDataProperties(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{        
        {{
        ?p <http://www.w3.org/2002/07/owl#equivalentProperty> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#equivalentProperty> ?p .
        }} 
        FILTER (isIRI(?p)) 
        }}""".format(prop=prop_uri)
    #Union is required in this case
    
    
    def getQueryForAllClassTypes(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o .
        FILTER (isIRI(?s) && isIRI(?o) 
        && str(?o) != 'http://www.w3.org/2002/07/owl#Ontology'
        && str(?o) != 'http://www.w3.org/2002/07/owl#AnnotationProperty'
        && str(?o) != 'http://www.w3.org/2002/07/owl#ObjectProperty'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Class'
        && str(?o) != 'http://www.w3.org/2002/07/owl#DatatypeProperty'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Restriction'
        && str(?o) != 'http://www.w3.org/2002/07/owl#NamedIndividual'
        && str(?o) != 'http://www.w3.org/2002/07/owl#Thing'
        )
        }"""
    #This makes the queries slower when large set of classes or invividuals:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
        
    
        
    
    def getQueryForIndividualClassTypes(self, ind_iri):
        
        return """SELECT ?o WHERE {{ <{ind}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o .
        FILTER (isIRI(?o) 
        && str(?o) != 'http://www.w3.org/2002/07/owl#NamedIndividual'
         && str(?o) != 'http://www.w3.org/2002/07/owl#Thing')
        }}""".format(ind=ind_iri)
    #Removed to speed up query:
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        
    
    
    def getQueryForAllSameAs(self):
        
        return """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2002/07/owl#sameAs> ?o .        
        filter( isIRI(?s) && isIRI(?o))  
        }"""
    #This makes the query very very slow for large instance sets:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> . 
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
    
    def getQueryForIndividualSameAs(self, ind_iri):
        
        return """SELECT ?i WHERE {{
        <{ind}> <http://www.w3.org/2002/07/owl#sameAs> ?i .
        filter( isIRI( ?i ) )            
        }}""".format(ind=ind_iri)
    #This makes the query very slow:
    #i <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
        
    
    
    def getQueryObjectRoleAssertions(self, prop_uri):
        
        return """SELECT ?s ?o WHERE {{ ?s <{prop}> ?o .
        filter( isIRI(?s) && isIRI(?o) )
        }}""".format(prop=prop_uri)
    #This makes the query unfeasible for large sets of instances:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> . 
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
    
    
    def getQueryDataRoleAssertions(self, prop_uri):
    
        return """SELECT ?s ?o WHERE {{ ?s <{prop}> ?o .
        filter( isIRI(?s) )        
        }}""".format(prop=prop_uri)
    #This makes the query unfeasible for large sets of instances:
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#NamedIndividual> .
        
    
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
    
    
    
    def getQueryForDomain(self, prop_uri):
        
        return """SELECT DISTINCT ?d WHERE {{ <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> ?d . 
        FILTER (isIRI(?d))
        }}""".format(prop=prop_uri)
    
    
    def getQueryForRange(self, prop_uri):
        
        return """SELECT DISTINCT ?r WHERE {{  
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> ?r .
        FILTER (isIRI(?r))
        }}""".format(prop=prop_uri)
    
    
    
        
    def getQueryForDomainAndRange(self, prop_uri):
        
        return """SELECT DISTINCT ?d ?r WHERE {{ <{prop}> <http://www.w3.org/2000/01/rdf-schema#domain> ?d . 
        <{prop}> <http://www.w3.org/2000/01/rdf-schema#range> ?r .
        FILTER (isIRI(?d) && isIRI(?r))
        }}""".format(prop=prop_uri)
        #To optimize query search:
        #?d <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        #?r <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .



    def getQueryForInverses(self, prop_uri):
        
        return """SELECT DISTINCT ?p WHERE {{        
        {{
        ?p <http://www.w3.org/2002/07/owl#inverseOf> <{prop}> .
        }}
        UNION
        {{
        <{prop}> <http://www.w3.org/2002/07/owl#inverseOf> ?p .
        }}
        filter(isIRI(?p)) 
        }}""".format(prop=prop_uri)
    #Union required
        
        
        
    #Restrictions on the right hand side: A sub R some A. 
    def getQueryForRestrictionsRHSSubClassOf(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?bn . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .        
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
        

    #Restrictions on the right hand side: A equiv R some A.
    def getQueryForRestrictionsRHSEquivalent(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s <http://www.w3.org/2002/07/owl#equivalentClass> ?bn . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .        
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
    #To improve scalability
    #?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> .
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    
    
    #Restrictions on the right hand side: A sub R some A. 
    def getQueryForDataRestrictionsRHSSubClassOf(self, prop_uri):
        
        return """SELECT DISTINCT ?s WHERE {{ 
        ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?bn . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        FILTER (isIRI(?s))        
        }}""".format(prop=prop_uri)
        

    #Restrictions on the right hand side: A equiv R some A.
    def getQueryForDataRestrictionsRHSEquivalent(self, prop_uri):
        
        return """SELECT DISTINCT ?s WHERE {{ 
        ?s <http://www.w3.org/2002/07/owl#equivalentClass> ?bn . 
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
        FILTER (isIRI(?s))
        }}""".format(prop=prop_uri)
    
    
    
    
    
    
        
    #Restrictions on the left hand side:  R some A sub A
    def getQueryForRestrictionsLHS(self, prop_uri):
        
        #Required to include subclassof between ?bn and ?s to avoid redundancy
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?bn <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s .        
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
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
    #To improve scalability
    #?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> .
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    
    
    
    #Restrictions on the right hand side: A sub R some (C or D)
    def getQueryForComplexRestrictionsRHSSubClassOf(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?bn .         
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
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
        
        
    
    #Restrictions on the right hand side: A equiv R some (C or D)
    def getQueryForComplexRestrictionsRHSEquivalent(self, prop_uri):
        
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?s <http://www.w3.org/2002/07/owl#equivalentClass> ?bn .         
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
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
    #To improve scalability
    #?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> .
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
     
        
    #Restrictions on the left hand side: R some (C or D) sub A
    def getQueryForComplexRestrictionsLHS(self, prop_uri):
        
        #Required to include subclassof between ?bn and ?s to avoid redundancy
        return """SELECT DISTINCT ?s ?o WHERE {{ 
        ?bn <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?s .         
        ?bn <http://www.w3.org/2002/07/owl#onProperty> <{prop}> .
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
    #To improve scalability
    #?bn <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction> .
    #?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    #?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        
    

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
    
    #path="/home/ernesto/Documents/OWL2Vec_star/OWL2Vec-Star-master/Version_0.1/"
    
    #uri_onto = path + "helis_v1.00.origin.owl"
    #file_projection  = path + "helis_v1.00.projection.ttl"
    
    
    #uri_onto = path + "foodon-merged.owl"
    #file_projection  = path + "foodon.projection.ttl"
    
    #uri_onto = path + "go.owl"
    #file_projection  = path + "go.projection.ttl"
    
    
    start_time = time.time()
    
    #Reasoner.HERMIT
    #Reasoner.STRUCTURAL
    #Reasoner.PELLET
    #Reasoner.NONE
    projection = OntologyProjection(uri_onto, reasoner=Reasoner.STRUCTURAL, only_taxonomy=False, bidirectional_taxonomy=True, include_literals=True, memory_reasoner='13351')
    logging.info("Time loading ontology (and classifying): --- %s seconds ---" % (time.time() - start_time))
    
    start_time = time.time()
    projection.extractProjection()
    logging.info("Time extracting projection: --- %s seconds ---" % (time.time() - start_time))
    
    start_time = time.time()
    #projection.getProjectionGraph()  gets RDFLib's Graph object with projection
    projection.saveProjectionGraph(file_projection)
    logging.info("Time saving projection: --- %s seconds ---" % (time.time() - start_time))
    
    
    #projection.extractTriplesFromComplexAxioms() 
    
        
        
        
