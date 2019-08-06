'''
Created on 28 Mar 2019

@author: ejimenez-ruiz
'''

from kg.entity import KG
from kg.entity import URI_KG


def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True
    
    
def getFilteredTypes(set_types, kgfilter=KG.All):
        if kgfilter==KG.All:
            return set_types
        else:
            kg_uri = URI_KG.uris[kgfilter.value]
            filtered_types = set()
            for t in set_types:
                if t.startswith(kg_uri):
                    filtered_types.add(t)
            
            return filtered_types 


def getFilteredResources(set_resources, kgfilter=KG.All):
        if kgfilter==KG.All:
            return set_resources
        else:
            kg_uri = URI_KG.uris_resource[kgfilter.value]
            filtered_resources = set()
            for r in set_resources:
                if r.startswith(kg_uri):
                    filtered_resources.add(r)
            
            return filtered_resources 
        
        
def getEntityName(uri):
    
    if "#" in uri:
        splits = uri.split("#")
        if len(splits[1])>0:
            return splits[1]
        else:
            return uri
        
    elif "/" in uri:
        splits = uri.split("/")
        
        i = len(splits)
        
        if len(splits[i-1])>0:
            return splits[i-1]
        else:
            return uri
        
    return uri
        
        
        

#print(getEntityName("http://dbpedia.org/ontology/Lake"))
#print(getEntityName("http://dbpedia.org/ontology#Lake"))
#print(getEntityName("http://dbpedia.org/ontology/"))
#print(getEntityName("http://dbpedia.org/ontology#"))  
#print(getEntityName("#/kaka"))  
        
        
        
        
        
        
        
        
    
    