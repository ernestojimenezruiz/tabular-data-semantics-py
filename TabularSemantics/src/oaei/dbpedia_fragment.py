'''
Created on 1 Aug 2019

@author: ejimenez-ruiz
'''

import csv
import datetime
from os import listdir
import os
from os.path import isfile, join
import os.path
import unicodedata

from constants import RDFS, OWL
from kg.endpoints import DBpediaEndpoint
from kg.entity import KG, KGEntity
from kg.lookup import DBpediaLookup
import pandas as pd
from rdflib import Graph, URIRef, BNode, Literal, term
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery
from urllib.parse import urlparse, quote
from util import utilities


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
        #prop: True -> isObjectProperty
        self.propertyType = dict()
        
        
        self.dbp_endpoint = DBpediaEndpoint()        
        self.lookup = DBpediaLookup()
        
        
        
        
    
    
    def isValidURI(self, str_uri):
        
        #use term._is_valid_unicode(str_uri)
        
        return term._is_valid_uri(str_uri) and self.isascii(str_uri)
    
    
    def isascii(self, string_original):
        
        string = self.strip_accents(string_original)  #to ignore accents 
            
        return len(string_original) == len(string.encode())
    
    
    
    def strip_accents(self, text):
            
        text = unicodedata.normalize('NFD', text)\
               .encode('ascii', 'ignore')\
               .decode("utf-8")
    
        return str(text)    
    
    
    #Precomputed
    def setUpLocalDBPediaGraph(self, file_ttl):
        self.localrdfgraph = Graph()
        self.localrdfgraph.parse(source=file_ttl, format='turtle')
        
    
    
    #To be computed
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
        
        
        wrong_file_name = ""
        
        try:
        
            if "?" in rdf_file_ouput:
                wrong_file_name = rdf_file_ouput.split("?")[0]
                os.rename(wrong_file_name, rdf_file_ouput)
            elif "#" in rdf_file_ouput:
                wrong_file_name = rdf_file_ouput.split("#")[0]
                os.rename(wrong_file_name, rdf_file_ouput)
            
                
            #print(wronf_file_name)
        except:
            print(wrong_file_name, rdf_file_ouput)



    def getTargetEntitiesCEA(self, cea_file):
        
        #Target entiteis for table
        self.targetEntities = dict()
        
        with open(cea_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            for row in csv_reader:
                
                if len(row)<4:
                    continue
                
                
                uris = row[3].split(" ")
                
                #entities per table
                key = row[0] #+ "-"+ row[1] + "-"+ row[2]
                
                if key not in self.targetEntities:  
                    self.targetEntities[key]=set()
                    
                self.targetEntities[key].update(uris)
                
                
        
    
    
    
    def getEntitiesAndCreateInstancesTable(self, table_name):
        
        if table_name in self.targetEntities:
        
            for ent in self.targetEntities[table_name]:
                
                if self.isValidURI(ent):
                    self.entities.add(ent)
                    e_uri = URIRef(ent)                    
                    self.rdfgraph.add( (e_uri, RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
                #else:
                #    pass
            
            
            
        
    

    def getEntitiesAndCreateInstances(self, cea_file):
        
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
                        pass
                        #print("Not valid URI?", uris[0], uris[i])
                    i+=1
                    
                    
                    
            for ent in self.entities:
                if self.isValidURI(ent):
                    e_uri = URIRef(ent)
                    self.rdfgraph.add( (e_uri, RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
                else:
                    pass
                    #print("Not valid URI:", ent)
                
            print("Number of entities: " + str(len(self.entities)))
    
    
    
    
    def getTargetColumns(self, cea_gt_file):
        
        self.target_column = dict()
               
        #An alternative is to automatically identify the left most column with an entity mention.
        #In this particular case we know the target
        with open(cea_gt_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
                        
            for row in csv_reader:
                
                if row[0] not in self.target_column or int(self.target_column[row[0]]) > int(row[1]):
                    self.target_column[row[0]] = row[1] 
                    
                    
                    
    
    def getEntitiesLookup(self, folder_cea_tables, cea_gt_file):
                
        #Lookup call for each cell in target column
        
        
        #Dictionary or cache to avoid repeated look-up
        visited_values = set() 
        
        
        #Get Target column
        self.getTargetColumns(cea_gt_file)
        
        csv_file_names = [f for f in listdir(folder_cea_tables) if isfile(join(folder_cea_tables, f))]
        
        i=0
        n=len(csv_file_names)
        t=[1, 5, 10, 50, 100, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]

        for csv_file in csv_file_names:
            
            i+=1
            
            if i in t:
                print("Getting look up entities for table %s of %s (%s)." % (i, n, datetime.datetime.now().time()))
            
            table_name = csv_file.replace(".csv", "")
            
            with open(join(folder_cea_tables, csv_file)) as csv_file:
            
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
                
                if table_name in self.target_column:
                    target_column = self.target_column[table_name]
                else: #End
                    continue
                    
                for row in csv_reader:
                    if len(row)<=int(target_column): 
                        continue
                    
                    if row[int(target_column)] not in visited_values:
                        
                        ##To avoid repetition
                        visited_values.add(row[int(target_column)])
                               
                        #Lookup top-3
                        dbpedia_entities = self.lookup.getKGEntities(row[int(target_column)], 3, '')
                        for ent in dbpedia_entities:
                            
                            if self.isValidURI(ent.getId()):
                                self.entities.add(ent.getId()) ##Add to entities to extract neighbours
                                
                                e_uri = URIRef(ent.getId())
                                self.rdfgraph.add( (e_uri, RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
                                
                                for cls_type in ent.getTypes(KG.DBpedia):
                                    self.rdfgraph.add( (e_uri, RDF.type, URIRef(cls_type)) )
                                
                            else:
                                #print("Not valid URI:", ent.getId())
                                pass
                            
                            
                            
                            
                            
                    
        
        print("Number of extended entities with look-up: " + str(len(self.entities)))
        
    
    
    def getEntitiesLookupForTable(self, csv_file):
                
        #Lookup call for each cell in target column
        
        
        #Dictionary or cache to avoid repeated look-up
        visited_values = set() 
            
        table_name = csv_file.replace(".csv", "")
            
        with open(join(folder_cea_tables, csv_file)) as csv_file:
            
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
                
                if table_name in self.target_column:
                    target_column = self.target_column[table_name]
                else: #End
                    return
                    
                for row in csv_reader:
                    if len(row)<=int(target_column): 
                        return
                    
                    if row[int(target_column)] not in visited_values:
                        
                        ##To avoid repetition
                        visited_values.add(row[int(target_column)])
                               
                        #Lookup top-3
                        dbpedia_entities = self.lookup.getKGEntities(row[int(target_column)], 3, '')
                        for ent in dbpedia_entities:
                            
                            if self.isValidURI(ent.getId()):
                                self.entities.add(ent.getId()) ##Add to entities to extract neighbours
                                
                                e_uri = URIRef(ent.getId())
                                self.rdfgraph.add( (e_uri, RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
                                
                                for cls_type in ent.getTypes(KG.DBpedia):
                                    self.rdfgraph.add( (e_uri, RDF.type, URIRef(cls_type)) )
                                
                            else:
                                #print("Not valid URI:", ent.getId())
                                pass
                            
                            
       
            
    
    
    def getTypes(self, cta_file):
        with open(cta_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            for row in csv_reader:
                
                if len(row)<3:
                    continue
                
                
                self.types.add(row[2])
                
            print("Number of types: " + str(len(self.types)))



    def getAssertionsForInstances(self, use_local_graph):
        
        #avoid some properties (see entity.py)

        #Differentiate between object and data properties? probably only necessary if literal or URI
        
        #Problem if range of property is not string. It will probably not match very well in any case.
        #Solution: remove domains and ranges in dbpedia ontology properties
        #Filter by dbpedia resources and types, eg: ignore URis from wikidata and types from other taxonomies.
        
        n=0
        
        l=[1, 5, 100, 1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000]
        
        
        for ent in self.entities:
            
            n+=1
            
            if self.isValidURI(ent):
            
                e_uri = URIRef(ent)
                
                #if n in l:
                #    print("Extracting neighbourhood for " + str(n) + ": " + ent + " (" + str(datetime.datetime.now().time()) + ")")
                
                
                if use_local_graph:
                    dict_results = self.getLocalTriplesForSubject(ent, 100)
                else:
                    dict_results = self.dbp_endpoint.getTriplesForSubject(ent, 100)
                
                
                
                for prop in dict_results:
                    
                    #if prop.startswith("http://dbpedia.org/"): #There are othe rinteresting properties: rdfs:labels, rdf:type, fiar:nameetc
                        
                        if self.isValidURI(prop):
                        
                            p_uri = URIRef(prop)
                            
                            isObjectProperty = self.identifyTypeOfProperty(prop)
                            
                            
                            for obj in dict_results[prop]:
                                
                                #Triple to resource
                                if obj.startswith("http") and isObjectProperty:
                                    
                                    if obj.startswith("http://dbpedia.org/resource/"):
                                    
                                        if self.isValidURI(obj):                                
                                            o_uri = URIRef(obj)                                
                                            self.rdfgraph.add( (e_uri, p_uri, o_uri) )
                                        else:
                                            #print("Not valid URI:", obj)
                                            pass
                                
                                elif not isObjectProperty: #Triple to Literal                            
                                    self.rdfgraph.add( (e_uri, p_uri, Literal(obj)) )
                                else:
                                    #print("Wrong object '%s' for property '%s' (isObjectProperty=%s)" % (obj, prop, isObjectProperty) )
                                    pass
                        else:
                            #print("Not valid URI:", prop)
                            pass
            else:
                pass
                #print("Not valid URI:", ent)
                    
                    
    def getLocalTriplesForSubject(self, ent, limit):
        
        query_str = "SELECT DISTINCT ?p ?o WHERE { <" + ent + "> ?p ?o  } limit " + str(limit)
        
        query_object = prepareQuery(query_str)#, initNs={CMR_QA.NAMESPACE_PREFIX : CMR_QA.BASE_URI})
            
        results = self.localrdfgraph.query(query_object)
        
        assertions = dict()
        
        
        for result in results:
            #print(str(result[0]), str(result[1]))
            prop = str(result[0])
            obj = str(result[1])
            if prop not in assertions:
                assertions[prop]=set()
            assertions[prop].add(obj)
        
        #print(assertions)
        
        return assertions
        
            
    def identifyTypeOfProperty(self, prop):
        
        if prop in self.propertyType:
            if self.propertyType[prop]:
                self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLOBJECTPROPERTY)) )
            else:
                self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLDATAPROPERTY)) )  
            
            return self.propertyType[prop]
        
        #Get statistics from endpoint        
        values = self.dbp_endpoint.getSomeValuesForPredicate(prop)
        
        n_values = len(values)
        n_uris = 0
        
        for v in values:
            if v.startswith("http"):
                n_uris+=1
        
        isObjectProperty =  (n_uris > (n_values/2))
        
        if isObjectProperty:
            self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLOBJECTPROPERTY)) )
            self.propertyType[prop]=True                                                                    
        else:
            self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLDATAPROPERTY)) )
            self.propertyType[prop]=False
            
        
        return isObjectProperty
        
        
    
    
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
                    #print("Not valid URI:", ent)
                    pass
        
        
        print("Number of extended entities with types: " + str(len(self.entities)))
                  


    #Using pre-extracted ttl/cache
    def localPropertyTypeExtractor(self):
    
            
        query_str = "SELECT DISTINCT ?p  WHERE { ?s ?p ?o . } "
        
        query_object = prepareQuery(query_str)#, initNs={CMR_QA.NAMESPACE_PREFIX : CMR_QA.BASE_URI})
        
        predicates = self.localrdfgraph.query(query_object)
        
        print("Using %s local predicates" % (len(predicates)))
        
        for p in predicates:
         
            #print(p)
            #continue
            prop = str(p[0])
            
            #print(prop)
            
            if not prop.startswith("http://dbpedia.org/"):  
                #we ignore other type of properties. Focus on dbpedia ones. 
                #Others will be trreates as annotation (rdfs:label, foaf:name) or specially (rdf:type)
                continue
            
        
            query_str = "SELECT ?value WHERE { ?s <" + prop + "> ?value . } limit 100"
            
            #print(query_str)
            #continue
            #print("lalala")
            
            query_object = prepareQuery(query_str)#, initNs={CMR_QA.NAMESPACE_PREFIX : CMR_QA.BASE_URI})
            
            values = self.localrdfgraph.query(query_object)
            
            n_values = len(values)
            n_uris = 0
            
            for v in values:
                #print(v[0])
                if str(v[0]).startswith("http"):
                    n_uris+=1
            
            
            if n_values==1:
                isObjectProperty = (n_uris == n_values)
            else:   
                isObjectProperty = (n_uris > (n_values/2))
            
            #print("New: " + prop)
            if isObjectProperty:                
                #self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLOBJECTPROPERTY)) )
                self.propertyType[prop]=True                                                                    
            else:
                #self.rdfgraph.add( (URIRef(prop),  RDF.type, URIRef(OWL.OWLDATAPROPERTY)) )
                self.propertyType[prop]=False
            
            #print(prop, self.propertyType[prop])
        



multiple_fragments=True
local_graph=True
ch_round=2

#Round 1
if ch_round==1:
    folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round1/"
    folder_cea_tables=folder+"CEA_Round1/"
    cea_gt = folder + "CEA_Round1_gt.csv"
    cta_gt = folder + "CTA_Round1_gt_for_CEA.csv"
    out_ttl = folder + "dbpedia_round1.ttl"

#Round 2
else:
    folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/"
    folder_cea_tables=folder+"Tables/"
    cea_gt = folder + "CEA/cea_gt.csv"
    cta_gt = folder + "CTA/cta_gt.csv"
    out_ttl = folder + "dbpedia_round2.ttl"

fragments_folder = folder + "dbpedia_fragments/"


#print(urlparse("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(urlparse("http://dbpedia.org/resource/Sad_ibn_Abi_Waqqas"))
#u = "http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas".encode("ascii", "replace")
#print(u.isascii())
#print(URIRef("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(term._is_valid_uri("http://dbpedia.org/resource/Sa`d_ibn_Abi_Waqqas"))
#print(URIRef("111"))


extractor = DBPediaExtractor()
        
#
'''
str1 = "NEC_µPD780C"
str1= "http://dbpedia.org/resource/Theorell,_Axel_Húgo_Teodor"
str1= "http://dbpedia.org/resource/Hall_&_Oates_(a)"
#str1 = "♥O◘♦♥O◘♦"
#str2 = "Python"
str1="http://dbpedia.org/resource/Win–loss_record_(pitching)"
str1="http://dbpedia.org/resource/Win-loss_record_(pitching)"
str1="http://dbpedia.org/resource/Chicago_White_Stockings_(1870–89)"
print(extractor.isValidURI(str1))
#print(extractor.isValidURI(str))
#print(quote(str))
print(extractor.strip_accents(str1))
obj="1"
prop="http://aaaa"
isObjectProperty=True
print("Wrong object '%s' for property '%s' (isObjectProperty=%s)" % (obj, prop, isObjectProperty) )

'''

#extractor.setUpLocalDBPediaGraph(out_ttl)
#extractor.getLocalTriplesForSubject("http://dbpedia.org/resource/Alex_Rodriguez", 100)

'''
csv_file_names = [f for f in listdir(folder_cea_tables) if isfile(join(folder_cea_tables, f))]

for csv_file in csv_file_names:
    
    fragment_name = csv_file.replace(".csv", ".ttl")
    fragment_name_full_path = join(fragments_folder, fragment_name)
    
    wrong_file_name = ""
        
    i=0
    #try:        
    if "?" in fragment_name_full_path:
            wrong_file_name = fragment_name_full_path.split("?")[0]
            os.rename(wrong_file_name, fragment_name_full_path)
            i+=1
    elif "#" in fragment_name_full_path:
            wrong_file_name = fragment_name_full_path.split("#")[0]
            os.rename(wrong_file_name, fragment_name_full_path)
            i+=1
            
    #except:
    #    print(wrong_file_name, fragment_name_full_path)    
    
print("renamed %s files" % (i))    
    
    #If already analysed
    #if (os.path.isfile(fragment_name_full_path) ):
    #    continue
'''

#'''
if multiple_fragments:
    
    extractor.setUpLocalDBPediaGraph(out_ttl)
    
    extractor.localPropertyTypeExtractor()
    
    #Get Target column
    extractor.getTargetColumns(cea_gt)
    #Target entities
    extractor.getTargetEntitiesCEA(cea_gt)
    
    csv_file_names = [f for f in listdir(folder_cea_tables) if isfile(join(folder_cea_tables, f))]
        
    i=0
    n=len(csv_file_names)
    t=[1, 2, 5, 10, 50, 100, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]

    for csv_file in csv_file_names:
        
        i+=1    
        if i in t:
            print("Getting look up entities for table %s of %s (%s)." % (i, n, datetime.datetime.now().time()))
        
        
        fragment_name = csv_file.replace(".csv", ".ttl")
        fragment_name_full_path = join(fragments_folder, fragment_name)
        
        #If already analysed
        if (os.path.isfile(fragment_name_full_path) ):
            if i in t:
                print("\tAlready created fragment.")
            continue
        
        
        
        
        
        extractor.entities = set()
        
        table_name = csv_file.replace(".csv", "")
        
        extractor.setUpRDFGraph()
        
        extractor.getEntitiesAndCreateInstancesTable(table_name)
        if i in t:
            print("\tNumber of entities: " + str(len(extractor.entities)))
        
        
        extractor.getEntitiesLookupForTable(csv_file) #look up for cells in tables
        if i in t:
            print("\tNumber of extended entities with look-up: " + str(len(extractor.entities)))        
    
        extractor.getAssertionsForInstances(local_graph) #create subset of neighbourhood triples
            
       
        
        extractor.saveRDFGrah(fragment_name_full_path)
        

else:
    
    extractor.setUpLocalDBPediaGraph(out_ttl)
    
    extractor.setUpRDFGraph()
    extractor.localPropertyTypeExtractor(out_ttl)
    
    
    extractor.getEntitiesAndCreateInstances(cea_gt) #create entity definitions from GT
    
    extractor.getTypes(cta_gt) #From CSV
    extractor.getInstancesForTypes()  #From endpoint + create triples
    
    
    extractor.getEntitiesLookup(folder_cea_tables, cea_gt) #look up for cells in tables
    
    
    extractor.getAssertionsForInstances(local_graph) #create subset of neighbourhood triples
    
    
    extractor.saveRDFGrah(out_ttl)
#''' 
        
        