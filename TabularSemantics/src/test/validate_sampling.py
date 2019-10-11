'''
Created on 2 Apr 2019

@author: ejimenez-ruiz
'''

from collections import OrderedDict
import json
import os
import time

from kg.endpoints import DBpediaEndpoint
from kg.entity import KG
from matching.kg_matching import Lookup, Endpoint
from util.utilities import *


class JSONUtilities(object):
    
    def __init__(self):
        
        self.smartlookup = Lookup()
        self.smartendpoint = Endpoint()
        self.dbpedia_ep = DBpediaEndpoint()
        
     
    def validateEntityToClasses(self, path, file_in, file_out):
        
        with open(path+file_in) as f:
            data = json.load(f)
            
        
        data_new = dict()    
        
            
        no_types=0
        empty_ref=0
        missing_cases=0
        wrong_cases=0
        empty_cases=0
        
        tmp_f = open(path + file_out.replace('.json','')+'.csv', 'w')
        tmp_f2 = open(path + file_out.replace('.json','')+'_issues.csv', 'w')
            
        for entity in data:
                
            types_tocheck = set(data[entity])
            types_ref = self.smartlookup.getTypesForEntity(entity, KG.DBpedia)
                
            if is_empty(types_ref):
                
                if is_empty(types_tocheck):
                    #Some issues with disambiguation pages
                    no_types+=1
                else:
                    ##Solved!
                    empty_ref+=1 #Some uris are redirects...
                    
                
                
                #We use the original types
                data_new[entity] = data[entity]
                 
                tmp_f.write('%s,%s\n' % (entity, ",".join(types_tocheck)))        
                
                continue
            
            
            #New set of corrected types
            data_new[entity] = list(types_ref) #json expects a list    
                
            
            tmp_f.write('%s,%s\n' % (entity, ",".join(types_ref)))
                
                
            #print("Checking", entity, len(types_ref), len(types_tocheck))
            #print("Checking %s: %s vs %s" % (entity, types_ref, types_tocheck))
                
                
            #Statistics
            missing = types_ref.difference(types_tocheck)
            wrong = types_tocheck.difference(types_ref)
                
            if len(missing) > 0 or len(wrong)>0:
                print("Issues with: " + entity)
                if len(missing) > 0:
                    print("\tMissing types: ", missing)
                    missing_cases+=1
                    if len(types_tocheck)==0:
                        empty_cases+=1
                    
                if len(wrong) > 0:
                    print("\tWrong types", wrong)
                    wrong_cases+=1
                
                tmp_f2.write("Entity,%s.\nMising,%s\nWrong:%s\n" % (entity, ",".join(missing), ",".join(wrong)))
        
        
        #We save the new types
        self.dumpJsonFile(data_new, path+file_out)
        
        tmp_f2.write("Cases with wrong types: %s\n" % (str(wrong_cases)))
        tmp_f2.write("Cases with missing types: %s\n" % (str(missing_cases)))
        tmp_f2.write("Cases with empty types : %s\n" % (str(empty_cases)))
        tmp_f2.write("Cases with empty new types: %s\n" % (str(empty_ref)))
        tmp_f2.write("Cases with no types at all: %s\n" % (str(no_types)))
        
        tmp_f.close()
        tmp_f2.close()        
            
        
        print("Cases with wrong types: " + str(wrong_cases))
        print("Cases with missing types: "+ str(missing_cases))
        print("Cases with empty types: "+ str(empty_cases))
        print("Cases with empty new types: "+ str(empty_ref))
        print("Cases with no types at all: "+ str(no_types))
        
        
        
    
    
    def createTriplesForClasses(self, path, class_file_r, class_file_s, file_out):
        
        
        tmp_f = open(path + file_out.replace('.json','')+'.csv', 'a+')
        
        
        #Read candidate classes
        classes = set()
        e_classes = json.load(open(path+class_file_r))
        for c_list in e_classes.values():
            for c in c_list:
                classes.add(c)
                
        #print(len(classes))
        
        e_classes = json.load(open(path+class_file_s))
        for c_list in e_classes.values():
            for c in c_list:
                classes.add(c)
                
        #print(len(classes))


        #Play with different numbers depending on the cost....
        #For each class extract 50-100-200 entities
        
        #Tests
        #entities = self.smartendpoint.getEntitiesForDBPediaClass("http://dbpedia.org/ontology/BaseballTeam", 100)
        #for e, label in entities.items():
        #    print(e, list(label)[0])
        #classes = set()
        
        
        
        #Dict to convert to jason
        #class_triples = dict()
        cache_file = path + file_out
        class_triples = json.load(open(cache_file)) if os.path.exists(cache_file) else dict()
        
        print("Class triples initial size", str(len(class_triples)))

         
        for c_uri in classes:
            
            print(c_uri)
            
            if c_uri in class_triples: #already analysed/cached
                print("\tAlready cached!")
                continue
            
            
            #if len(class_triples)>5:
            #    break
            
            
            
            i = time.time()
            
            tmp_f.write('%s\n' % (c_uri))
            
            #Dictionary entity-label
            entities = self.smartendpoint.getEntitiesForDBPediaClass(c_uri, 500)
                
            
            #For each above entity (?o) extract triples ?s ?p ?o, together with the label of ?o
            #Extract from 10-50 triples for entity, filter ?p NOT IN: show top ones we aim at discard
            
            triples = list()
            
            for object_uri in entities:
                '''
                '''
                #label 
                label = list(entities[object_uri])[0]
                
                #Triples for object entity
                subjects_predicates = self.dbpedia_ep.getTriplesForObject(object_uri, 50)
                
                for subject in subjects_predicates:
                    for predicate in subjects_predicates[subject]:
                        
                        triple = [subject, predicate, object_uri, label]
                        triples.append(triple)
                        
                        tmp_f.write('%s\n' % (",".join(triple)))
                           
            
            #end for entities
        
            print("\tTriples", len(triples))
            class_triples[c_uri] = triples
            
            #We dump, so that if it we breaks we can continue from there
            self.dumpJsonFile(class_triples, path+file_out)
           
            e = time.time()
            
            print("Time:", e-i)
            
        
        #end for classes
        
        
        #We save the new triples
        tmp_f.close()
        print(len(class_triples), path+file_out)
        self.dumpJsonFile(class_triples, path+file_out)
        
    

                
                
    #TBC
    def validateClassTriples(self, file):
        
        
        
        
        with open(file) as f:
            data = json.load(f)
            
            
            predicate_count=dict()
            
            n_triples = 0
            
            empty_entries = 0
            
            for entity in data:
                subjects = set()
                predicates = set()
                objects = set()
                
                print(entity, len(data[entity]))
                
                if len(data[entity])==0:
                    empty_entries+=1
                
                n_triples+=len(data[entity])
                
                n_triples_class=0
                
                for triple in data[entity]: 
                    
                    if triple[1] in URI_KG.avoid_predicates:
                        continue
                    
                    if not triple[1].startswith(URI_KG.dbpedia_uri) and not triple[1].startswith(URI_KG.dbpedia_uri_property):
                        continue
                    
                    n_triples_class+=1
                    
                    subjects.add(triple[0])
                    
                    if triple[1] not in predicate_count:
                        predicate_count[triple[1]]=0
                    
                    predicate_count[triple[1]]+=1
                    
                    predicates.add(triple[1])
                    objects.add(triple[2])
                    #print("\t",data[entity][0])
                
                print("\t Different Triples, Subjects, predicates, objects: %s, %s, %s, %s" % (str(n_triples_class), str(len(subjects)), str(len(predicates)), str(len(objects))))
             
            
            print("Empty entries", empty_entries)    
            
            
            predicate_count_sorted = OrderedDict(sorted(predicate_count.items(), key=lambda x: x[1]))
            
            #for k, v in predicate_count_sorted.items():
            #    print(k, v)
                
                
            print(len(data), n_triples)

    def dumpJsonFile(self, data_json, file):            
        with open(file, "w") as write_file:
            json.dump(data_json, write_file)




if __name__ == '__main__':
    
    path="/home/ejimenez-ruiz/git/tabular-data-semantics-py/TabularSemantics/test-data/"
    
    #Particular samples real: 17007 entities
    file_ps_r = "RData_entity_class.json"
    file_ps_r_new = "RData_entity_class_fixed.json"
    
    #Particular samples synthetic: 11593 entities
    file_ps_s = "SData_entity_class.json"
    file_ps_s_new = "SData_entity_class_fixed.json"
    
    file_GT_s = "SData_Type.json"
    file_GT_s_new = "SData_Type_fixed.json"
    
    #General samples #339 classes
    file_gs = "class_triple.json"
    file_gs_triples_new = "class_triple_fixed.json"
    
    init = time.time()
    
    util = JSONUtilities()
    
    #util.validateEntityToClasses(path, file_ps_s, file_ps_s_new)   #SDATA
    #util.validateEntityToClasses(path, file_ps_r, file_ps_r_new)   #RDATA
    #util.validateEntityToClasses(path, file_GT_s, file_GT_s_new)   #SDATA GT
    #util.validateEntityToClasses(path, "small_test.json", "small_test_fixed.json") #Test
    
    
    
    #util.validateClassTriples(path+file_gs)  #Statistics
    
    
    
    util.createTriplesForClasses(path, file_ps_r_new, file_ps_s_new, file_gs_triples_new)
    
    
    
    
    end = time.time()
    print("Time:", end-init)
    
    