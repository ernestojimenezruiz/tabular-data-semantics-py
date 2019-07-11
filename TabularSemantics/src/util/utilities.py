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