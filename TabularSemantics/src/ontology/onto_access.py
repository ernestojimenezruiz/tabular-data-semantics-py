'''
Created on 2 Jan 2019

@author: ejimenez-ruiz
'''
from owlready2 import *
import rdflib
from rdflib.plugins.sparql import prepareQuery
import logging
from enum import Enum


class Reasoner(Enum):
    HERMIT=0 #Not really adding the right set of entailments
    PELLET=1 #Slow for large ontologies
    STRUCTURAL=2  #Basic domain/range propagation
    NONE=3 #No reasoning


class OntologyAccess(object):
    '''
    classdocs
    '''
   


    def __init__(self, urionto):
        
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        
        self.urionto = urionto        
        #List from owlready2
        #onto_path.append(pathontos) #For local ontologies
        
    
    
    def getOntologyIRI(self):
        return self.urionto
    
    
    
    def loadOntology(self, reasoner=Reasoner.NONE, memory_java='10240'):   
        
        #self.world = World()
        
        
        #Method from owlready
        self.onto = get_ontology(self.urionto).load()
        #self.onto = self.world.get_ontology(self.urionto).load()
        #self.onto.load()
        
        #self.classifiedOnto = get_ontology(self.urionto + '_classified')
        owlready2.reasoning.JAVA_MEMORY=memory_java
        owlready2.set_log_level(9)     
            
        if reasoner==Reasoner.PELLET:
            
            try:
                with self.onto:  #it does add inferences to ontology
                    
                    # Is this wrt data assertions? Check if necessary
                    # infer_property_values = True, infer_data_property_values = True
                    logging.info("Classifying ontology with Pellet...")
                    sync_reasoner_pellet() #it does add inferences to ontology
                   
                    unsat = len(list(self.onto.inconsistent_classes()))
                    logging.info("Ontology successfully classified.")
                    if unsat > 0:
                        logging.warning("There are " + str(unsat) + " unsatisfiabiable classes.")
            except:                              
                logging.info("Classifying with Pellet failed.")
        
        elif reasoner==Reasoner.HERMIT:
                            
                try:                    
                    with self.onto:  #it does add inferences to ontology
                                  
                        logging.info("Classifying ontology with HermiT...")
                        sync_reasoner() #HermiT doe snot work very well.... 
    
                        unsat = len(list(self.onto.inconsistent_classes()))
                        logging.info("Ontology successfully classified.")
                        if unsat > 0:
                            logging.warning("There are " + str(unsat) + " unsatisfiabiable classes.")
                
                except:
                    
                    logging.info("Classifying with HermiT failed.")
                    
        ##End Classification
        ####
            
        #report problem with unsat (Nothing not declared....)
        #print(list(self.onto.inconsistent_classes()))
        
        self.graph = default_world.as_rdflib_graph()
        logging.info("There are {} triples in the ontology".format(len(self.graph)))
        #self.graph = self.world.as_rdflib_graph()

        
    
    
    def getOntology(self):
        return self.onto
    
    #def getInferences(self):
    #    return self.inferences
    
    
    #Does not seem to be a better way (or working way) according to the documentation...
    def getClassByURI(self, uri):
        
        for cls in list(self.getOntology().classes()):
            if (cls.iri==uri):
                return cls
            
        return None
            
    
    def getClassByName(self, name):
        
        for cls in list(self.getOntology().classes()):
            if (cls.name.lower()==name.lower()):
                return cls
            
        return None
    
    
    
    def getEntityByURI(self, uri):
        
        for cls in list(self.getOntology().classes()):
            if (cls.iri==uri):
                return cls
                
        for prop in list(self.getOntology().properties()):
            if (prop.iri==uri):
                return prop
                
        return None
    
    
    def getEntityByName(self, name):
        
        for cls in list(self.getOntology().classes()):
            if (cls.name.lower()==name.lower()):
                return cls
    
        for prop in list(self.getOntology().properties()):
            if (prop.name.lower()==name.lower()):
                return prop
    
    
        return None
    
    
    
    def getClassObjectsContainingName(self, name):
        
        classes = []
        
        for cls in list(self.getOntology().classes()):
            if (name.lower() in cls.name.lower()):
                classes.append(cls)
            
        return classes
    
    
    def getClassIRIsContainingName(self, name):
        
        classes = []
        
        for cls in list(self.getOntology().classes()):
            if (name.lower() in cls.name.lower()):
                classes.append(cls.iri)
            
        return classes
    
    
    def getAncestorsURIsMinusClass(self,cls):
        ancestors_str = self.getAncestorsURIs(cls)
        
        ancestors_str.remove(cls.iri)
        
        return ancestors_str
    
    
    
    def getAncestorsURIs(self,cls):
        ancestors_str = set()
        
        for anc_cls in cls.ancestors():
            ancestors_str.add(anc_cls.iri)
        
        return ancestors_str    
    
    
    def getDescendantURIs(self,cls):
        descendants_str = set()
        
        for desc_cls in cls.descendants():
            descendants_str.add(desc_cls.iri)
        
        return descendants_str    
        
        
    def getDescendantNames(self,cls):
        descendants_str = set()
        
        for desc_cls in cls.descendants():
            descendants_str.add(desc_cls.name)
    
        return descendants_str
    
    
    
    def getDescendantNamesForClassName(self, cls_name):
        
        cls = self.getClassByName(cls_name)
        
        descendants_str = set()
        
        for desc_cls in cls.descendants():
            descendants_str.add(desc_cls.name)
    
        return descendants_str
    
    
    
    def isSubClassOf(self, sub_cls1, sup_cls2):
        
        if sup_cls2 in sub_cls1.ancestors():
            return True
        return False
    
    
    def isSuperClassOf(self, sup_cls1, sub_cls2):
        
        if sup_cls1 in sub_cls2.ancestors():
            return True
        return False
    
    
    
    def getDomainURIs(self, prop):
        
        domain_uris = set()
        
        for cls in prop.domain:                       
            #for c in cls.Classes:
            #    print(c)
            try:
                domain_uris.add(cls.iri)
            except AttributeError:
                pass
        
        return domain_uris


    def getDatatypeRangeNames(self, prop):
        
        range_uris = set()
        
        for cls in prop.range:
            range_uris.add(cls.name)  #datatypes are returned without uri

        return range_uris       
    
    
    #Only for object properties
    def getRangeURIs(self, prop):
        
        range_uris = set()
        
        for cls in prop.range:
            
            try:
                range_uris.add(cls.iri)  
            except AttributeError:
                pass

        return range_uris
    
    
    def geInverses(self, prop):
        
        inv_uris = set()
        
        for p in prop.inverse:
            inv_uris.add(p.iri)  

        return inv_uris
    
    
    def getClasses(self):        
        return self.getOntology().classes()
    
    def getDataProperties(self):        
        return self.getOntology().data_properties()
    
    def getObjectProperties(self):        
        return self.getOntology().object_properties()
    
    def getIndividuals(self):        
        return self.getOntology().individuals()
        
    
    #Ontology graph representation (from RDFlib). Not to confuse with projection graph
    def getGraph(self):
        return self.graph
    
    
        
    def queryGraph(self, query):
        
        #query_owlready() 
        
        #results = self.graph.query("""SELECT ?s ?p ?o WHERE { ?s ?p ?o . }""")
        results = self.graph.query(query)
        
        
        return list(results)
        
                
        #print(r)
        #for r in results:
        #    print(r.labels)
        #    print(r[0]) 
        
        
        

class DBpediaOntology(OntologyAccess):
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getOntologyIRI())
        
        
    def getOntologyIRI(self):
        return "http://www.cs.ox.ac.uk/isg/ontologies/dbpedia.owl"
    
    
    def getAncestorsURIs(self,cls):
        ancestors_str = set()
        
        for anc_cls in cls.ancestors():
            ancestors_str.add(anc_cls.iri)
        
        agent = "http://dbpedia.org/ontology/Agent"
        if agent in ancestors_str:
            ancestors_str.remove(agent)
        
        return ancestors_str
    
    
class SchemaOrgOntology(OntologyAccess):
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getOntologyIRI())
        
        
    def getOntologyIRI(self):
        return "http://www.cs.ox.ac.uk/isg/ontologies/schema.org.owl"
        
    
    
        
    
    
    

   
    

if __name__ == '__main__':

    #folder_ontos="/home/ejimenez-ruiz/eclipse-python/TabularSemantics/ontologies/"
    #uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/dbpedia.owl"
    #uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/schema.org.owl"
    uri_onto = "https://zenodo.org/record/3925544/files/SiriusGeoOnto_v1.0.owl"
    uri_onto = "/home/ernesto/Documents/ImageAnnotation-SIRIUS/Images_annotations_snapshot/last_version_onto/SiriusGeoOnto_v1.0.owl"
    uri_onto = "/home/ernesto/ontologies/test_projection.owl"
    #uri_onto="file:///home/ejimenez-ruiz/eclipse-python/TabularSemantics/ontologies/dbpedia.owl"
    #uri_onto="file:///home/ejimenez-ruiz/eclipse-python/TabularSemantics/ontologies/schema.org.owl"
    
    #onto_access = OntologyAccess(uri_onto)
    
    
    #onto_access = DBpediaOntology()
    #onto_access = SchemaOrgOntology()
    onto_access = OntologyAccess(uri_onto)    
    onto_access.loadOntology(True) #Classify True
        
    print(dir(onto_access.getOntology()))
    
    
    query = """SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"""
    #query = """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .
    #    ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
    #    ?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
    #    }"""
    results = onto_access.queryGraph(query)   
    
    for r in results:
        print(r)
        #print(r.labels)
        #print(r[0]) 
        #print(r.s) 
    
    
    #.graph, get_triples
    #general_axioms
    #'annotation_properties', 'base_iri', 'classes', 'data_properties', 'destroy', 'different_individuals', 
    #'disjoint_classes', 'disjoint_properties', 'disjoints', 'general_axioms', 'get_children_of', 
    #'get_imported_ontologies', 'get_instances_of', 'get_namespace', 'get_parents_of', 'get_python_module', 
    #'get_triples', 'graph', 'imported_ontologies', 'inconsistent_classes', 'indirectly_imported_ontologies', 
    #'individuals', 'load', 'loaded', 'metadata', 'name', 'object_properties', 'ontology', 'properties', 
    #'python_module', 'rules', 'save', 'search', 'search_one', 'set_imported_ontologies', 'set_python_module', 
    #'storid', 'variables', 'world']
    
    
    #for ax in onto_access.getOntology().general_axioms():
    #    print(ax)
    #    print(dir(ax))
    #    print(ax.subclasses())
        #print(ax.ancestors())
        #print(ax.value)
        #print(ax.type)
    #    print()
        
    
    #for t in onto_access.getOntology().get_triples():
    #    print(t)
    
    #if True:
    #    sys.exit()
        
    
    
    
    #print(len(list(onto_access.getOntology().object_properties())))
    

    
    
    
    
    
    for prop in list(onto_access.getOntology().data_properties()):
        #print("LALALA")
        print(prop)
        print("isa: " + str(prop.is_a))  #filter and keep only obj properties (filter by namespace)
        print("equiv: " + str(prop.equivalent_to)) #In many cases the equivalent may be the inverse of the inverse...., try/except
        print("relations: ")
        for relation in prop.get_relations():
            print("\t" + str(relation))
        print()
    
    
    
    
    
    
    for prop in list(onto_access.getOntology().object_properties()):
        #print("LALALA")
        print(prop)
        print("domain: " + str(onto_access.getDomainURIs(prop)))
        print("range: " + str(onto_access.getRangeURIs(prop)))
        print("inverses: " + str(prop.inverse))
        print("isa: " + str(prop.is_a))  #filter and keep only obj properties (filter by namespace)
        print("equiv: " + str(prop.equivalent_to)) #In many cases the equivalent may be the inverse of the inverse...., try/except
        print("relations: ")
        for relation in prop.get_relations():
            print("\t" + str(relation))
        print()
    
    
    for cls in list(onto_access.getOntology().classes()):
        print(cls)
        print(dir(cls))
        
        print(cls.get_properties(cls))
        #Access via attribute. Use try except
        print("label: " + str(cls.label))
        
        #for prop in cls.get_properties(cls): 
        #    print(prop.iri)
        #    print(prop.get_relations())
            #for relation in prop.get_relations():
            #    print("\t" + str(relation))
                
    
                
        #print("inferred parents: " + str(onto_access.getInferences().get_parents_of(cls)))
        print("parents: " + str(onto_access.getOntology().get_parents_of(cls)))
        print("isa: " + str(cls.is_a))  #Filter isa?
        for cls_exp in cls.is_a:
            
            print(dir(cls_exp))
            
            try:
                #print("aaaa"+str(cls_exp.type))
                print("get_is_a(): " + str(cls_exp.get_is_a()))
                print("Classes: " + str(cls_exp.Classes))
                for a in cls_exp.get_is_a():
                    print(a)
            except AttributeError:
                pass
            
            
            try:
                print("\t" + cls_exp.name)   ##How to access restrictions?
            except AttributeError:
                
                try:
                    #dir(to get all objects)
                    print("\t"+ str(cls_exp))
                    #print("\t\t"+ str(cls_exp.ancestors))
                    print("\t\t cardinality: "+ str(cls_exp.cardinality))
                    #print("\t\t"+ str(cls_exp.is_a))
                    print("\t\t"+ str(cls_exp.property))
                    #print("\t\t"+ str(cls_exp.subclasses))
                    print("\t\t restriction: "+ str(cls_exp.type))
                    print("\t\t"+ str(cls_exp.value))
                    print("\t\t\t"+ str(dir(cls_exp.value)))
                    #try access iri otherwise pass as above              
                    #print(\n', 'cardinality', 'destroy', 'is_a', 'ontology', 'property', 'storid', 'subclasses', 'type', 'value')
                    #some: 24, only: 25
                except AttributeError:
                    pass
            
        print("equiv: " + str(cls.equivalent_to))
        
        for cls_exp in cls.equivalent_to:
            
            print(dir(cls_exp))
            
            #print("aaa" + str(cls_exp.get_is_a()))
            
            try:
                #print("aaaa"+str(cls_exp.type))
                print("get_is_a(): " + str(cls_exp.get_is_a()))
                print("Classes: " + str(cls_exp.Classes))
                for a in cls_exp.get_is_a():
                    print(a)
            except AttributeError:
                pass
            try:
                print("\t" + cls_exp.name)   ##How to access restrictions?
            except AttributeError:
                
                try:
                    #dir(to get all objects)
                    print("\t"+ str(cls_exp))
                    print("\t"+ str(cls_exp.type))
                    #print("\t\t"+ str(cls_exp.ancestors))
                    print("\t\t"+ str(cls_exp.cardinality))
                    #print("\t\t"+ str(cls_exp.is_a))
                    print("\t\t"+ str(cls_exp.property))
                    #print("\t\t"+ str(cls_exp.subclasses))
                    print("\t\t restriction: "+ str(cls_exp.type))
                    print("\t\t"+ str(cls_exp.value))
                    print("\t\t\t"+ str(dir(cls_exp.value)))
                    #try access iri otherwise pass as above              
                    #print(\n', 'cardinality', 'destroy', 'is_a', 'ontology', 'property', 'storid', 'subclasses', 'type', 'value')
                    #some: 24, only: 25
                except AttributeError:
                    pass
        
        print("disjoint: " + str(cls.disjoints())) #returns pairs <cls, disj> -> ignore?
        print("instances: " + str(cls.instances()))
        print()
    
    
    
    #Annotations
    #cls.nameannotaion -> cls.label, cls.altLabel, cls.prefLabel
    
    
    
    #Roleassertions from an instance
    #get_properties()
    #get_inverse_properties()
    #instance.isa to get types
    
    #Properties
    #inverse_property
    
    
    #How to deal with subproperties? ->propagate A R B -> A S B if R < S
    
    # get_relations() gets pairs subject -object (role assertions) for a property
    
    #sames_as -> equivalen_to for instances
    
    
    
    #print(onto_access.getClassIRIsContainingName("player"))
    #print(onto_access.getClassIRIsContainingName("actor"))
    
    
    
    #print(onto_access.getClassByName("City"))
    #print(onto_access.getClassByName("City").descendants())
    #print(onto_access.getClassByName("City").ancestors())
    #print(onto_access.getDescendantURIs(onto_access.getClassByName("City")))
    #print(onto_access.getAncestorsURIs(onto_access.getClassByName("City")))
    
    
