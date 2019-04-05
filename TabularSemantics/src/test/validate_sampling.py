'''
Created on 2 Apr 2019

@author: ejimenez-ruiz
'''

import json

from matching.kg_matching import Lookup
from kg.entity import KG
from util.utilities import *
import time




class JSONUtilities(object):
    
    def __init__(self):
        
        self.lookup = Lookup()
        
     
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
            types_ref = self.lookup.getTypesForEntity(entity, KG.DBpedia)
                
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
        
        
        
        
        
                
                
    #TBC
    def validateClassTriples(self, file):
        with open(file) as f:
            data = json.load(f)
            
            i=0
            
            for entity in data:
                print(entity, len(data[entity]))
                print("\t",data[entity][0])
                i+=1
            print(i)
            
            

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
    
    #General samples #339 classes
    file_gs = "class_triple.json"
    
    init = time.time()
    
    util = JSONUtilities()
    
    #util.validateEntityToClasses(path, file_ps_s, file_ps_s_new)
    util.validateEntityToClasses(path, file_ps_r, file_ps_r_new)
    #util.validateEntityToClasses(path, "small_test.json", "small_test_fixed.json")
    
    
    
    #util.validateClassTriples(file_gs)  
    
    end = time.time()
    print("Time:", end-init)
    
    