from ontology.onto_access import OntologyAccess 
    

#uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/dbpedia.owl"
#uri_onto="http://www.cs.ox.ac.uk/isg/ontologies/schema.org.owl"
uri_onto = "https://zenodo.org/record/3925544/files/SiriusGeoOnto_v1.0.owl"
uri_onto = "/home/ernesto/ontologies/test_projection.owl"

#onto_access = OntologyAccess(uri_onto)


#onto_access = DBpediaOntology()
#onto_access = SchemaOrgOntology()
onto_access = OntologyAccess(uri_onto)    
onto_access.loadOntology(True) #Classify True
        
print(dir(onto_access.getOntology()))
    

query = """SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"""
#query = """SELECT ?s ?o WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?o .
#?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> . 
#?o <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .  
#}"""
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
    #print(ax)
    #print(dir(ax))
    #print(ax.subclasses())
    #print(ax.ancestors())
    #print(ax.value)
    #print(ax.type)
    #print()


#for t in onto_access.getOntology().get_triples():
    #print(t)
    
#if True:
    #sys.exit()
    



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
    
    
