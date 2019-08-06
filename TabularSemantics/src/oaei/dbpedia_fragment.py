'''
Created on 1 Aug 2019

@author: ejimenez-ruiz
'''

from rdflib import Graph, URIRef, BNode, Literal, term
from rdflib.namespace import RDF
from constants import RDFS, OWL

import csv
import pandas as pd

from os import listdir
from os.path import isfile, join
from util import utilities
import os
from urllib.parse import urlparse


from kg.endpoints import DBpediaEndpoint


class DBPediaExtractor(object):
    '''
    classdocs
    '''

    #Steps
    # Read entities from GT, include redirections and add same_as axioms
    # Query for types
    # Query for 1 level of relationships, filter those non in dbpedia ontology

    def __init__(self):
        '''
        Constructor
        '''
        #Set up
        #self.setUpRDFGraph()
        self.entities = set()
        self.types = set()
        
        
        self.dbp_endpoint = DBpediaEndpoint()
    
    
    def isValidURI(self, str_uri):
        return term._is_valid_uri(str_uri)
    
    def setUpRDFGraph(self):
        self.rdfgraph = Graph()
        #self.rdfgraph.bind(TabularToRDF.NAMESPACE_PREFIX, TabularToRDF.BASE_URI)
        self.rdfgraph.bind("foaf", "http://xmlns.com/foaf/0.1/")
        self.rdfgraph.bind("dbp", "http://dbpedia.org/property/")
        self.rdfgraph.bind("dbr", "http://dbpedia.org/resource/")
        self.rdfgraph.bind("dbo", "http://dbpedia.org/ontology/")
        self.rdfgraph.bind("owl", "http://www.w3.org/2002/07/owl#")
        
        
    
    
    def saveRDFGrah(self, rdf_file_ouput):
        #output same table name as ttl
        self.rdfgraph.serialize(str(rdf_file_ouput), format='turtle')#xml,turtle


    def getEntities(self, cea_file):
        
        with open(cea_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            for row in csv_reader:
                
                if len(row)<4:
                    continue
                
                
                uris = row[3].split(" ")
                
                for i in range(len(uris)):
                    self.entities.add(uris[i])
                    
                i=1
                while i<len(uris):
                    
                    if self.isValidURI(uris[0]) and self.isValidURI(uris[i]):
                        e_uri1 = URIRef(uris[0])
                        e_uri2 = URIRef(uris[i])
                        self.rdfgraph.add( (e_uri1, URIRef(OWL.SAMEAS), e_uri2) )
                    else:
                        print("Not valid URI?", uris[0], uris[i])
                    i+=1
                    
                    
                    
            for ent in self.entities:
                if self.isValidURI(ent):
                    e_uri = URIRef(ent)
                    self.rdfgraph.add( (e_uri, RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
                else:
                    print("Not valid URI:", ent)
                
            print("Number of entities: " + str(len(self.entities)))
                
                
            
    
    
    def getTypes(self, cta_file):
        with open(cta_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            for row in csv_reader:
                
                if len(row)<3:
                    continue
                
                
                self.types.add(row[2])
                
            print("Number of types: " + str(len(self.types)))



    def getAssertionsForInstances(self):
        
        #avoid some properties (see entity.py)

        #Differentiate between object and data properties? probably only necessary if literal or URI
        
        #Problem if range of property is not string. It will probably not match very well in any case.
        #Solution: remove domains and ranges in dbpedia ontology properties
        #Filter by dbpedia resources and types, eg: ignore URis from wikidata and types from other taxonomies.
        
        n=0
        
        l=[100, 1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000]
        
        
        for ent in self.entities:
            
            n+=1
            
            if self.isValidURI(ent):
            
                e_uri = URIRef(ent)
                
                if n in l:
                    print("Extracting neighbourhood for " + str(n) + ": " + ent)
                
                dict_results = self.dbp_endpoint.getTriplesForSubject(ent, 100)
                
                for prop in dict_results:
                    
                    #if prop.startswith("http://dbpedia.org/"):
                    
                        p_uri = URIRef(prop)
                        
                        for obj in dict_results[prop]:
                            
                            #Triple to resource
                            if obj.startswith("http"):
                                
                                if obj.startswith("http://dbpedia.org/resource/"):
                                
                                    if self.isValidURI(obj):                                
                                        o_uri = URIRef(obj)                                
                                        self.rdfgraph.add( (e_uri, p_uri, o_uri) )
                                    else:
                                        print("Not valid URI:", ent)
                            
                            else: #Triple to Literal                            
                                self.rdfgraph.add( (e_uri, p_uri, Literal(obj)) )
            else:
                print("Not valid URI:", ent)
                    
                    
                    
            
            
        
        
        
    
    
    def getInstancesForTypes(self):
        #Use basic method
        
        additional_entities = set()
        
        for cls in self.types:
            
            #print("Extracting members for: " + cls)
            additional_entities = self.dbp_endpoint.getEntitiesForType(cls, 0, 100)
            
            #We also want to extract neighbourhood
            self.entities.update(additional_entities)
            
            for ent in additional_entities:
                
                if self.isValidURI(ent):
                    e_uri = URIRef(ent)
                    if cls.startswith("http://dbpedia.org/"):
                        self.rdfgraph.add( (e_uri, RDF.type, URIRef(cls)) )
                else:
                    print("Not valid URI:", ent)
        
        
        print("Number of extended entities: " + str(len(self.entities)))
                  


#Round 1
folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round1/"
cea_gt = folder + "CEA_Round1_gt.csv"
cta_gt = folder + "CTA_Round1_gt_for_CEA.csv"
out_ttl = folder + "dbpedia_round1.ttl"

#Round 2
#folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/"
#cea_gt = folder + "CEA/cea_gt.csv"
#cta_gt = folder + "CTA/cta_gt.csv"
#out_ttl = folder + "dbpedia_round2.ttl"



#print(urlparse("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(urlparse("http://dbpedia.org/resource/Sad_ibn_Abi_Waqqas"))
#u = "http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas".encode("ascii", "replace")
#print(u.isascii())
#print(URIRef("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(term._is_valid_uri("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(URIRef("111"))
        

extractor = DBPediaExtractor()

extractor.setUpRDFGraph()

extractor.getEntities(cea_gt) #create entity definitions

extractor.getTypes(cta_gt) #From CSV
extractor.getInstancesForTypes()  #From endpoint + create triples

extractor.getAssertionsForInstances() #create subset of neighbourhood triples


extractor.saveRDFGrah(out_ttl)
    
        
        