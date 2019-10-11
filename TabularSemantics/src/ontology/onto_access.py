'''
Created on 2 Jan 2019

@author: ejimenez-ruiz
'''
from owlready2 import *


class OntologyAccess(object):
    '''
    classdocs
    '''


    def __init__(self, urionto):
        
        self.urionto = urionto
        
        #List from owlready2
        #onto_path.append(pathontos) #For local ontologies
        
    
    
    def loadOntology(self, classify):   
        
        self.onto = get_ontology(self.urionto)
        self.onto.load()
        
        #self.classifiedOnto = get_ontology(self.urionto + '_classified')        
        if classify:
            with self.onto:
                sync_reasoner()  #it does add inferences to ontology
            
        #report problem with unsat (Nothing not declared....)
        #print(list(self.onto.inconsistent_classes()))
        
    
    
    def getOntology(self):
        return self.onto
    
    
    #Does not seem to be a better way (or working way) according to the documentation...
    def getClassByURI(self, uri):
        
        for cls in list(self.getOntology().classes()):
            if (cls.iri==uri):
                return cls
            
        return None
            
    
    def getClassByName(self, name):
        
        for cls in list(self.getOntology().classes()):
            if (cls.name==name):
                return cls
            
        return None
    
    
    
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
    uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/dbpedia.owl"
    uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/schema.org.owl"
    #uri_onto="file:///home/ejimenez-ruiz/eclipse-python/TabularSemantics/ontologies/dbpedia.owl"
    #uri_onto="file:///home/ejimenez-ruiz/eclipse-python/TabularSemantics/ontologies/schema.org.owl"
    
    #onto_access = OntologyAccess(uri_onto)
    
    
    onto_access = DBpediaOntology()
    onto_access = SchemaOrgOntology()
    
    onto_access.loadOntology(True)
    
    
    
    print(onto_access.getClassByName("City"))
    print(onto_access.getClassByName("City").descendants())
    print(onto_access.getClassByName("City").ancestors())
    print(onto_access.getDescendantURIs(onto_access.getClassByName("City")))
    print(onto_access.getAncestorsURIs(onto_access.getClassByName("City")))
    
    
