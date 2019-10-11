'''
Created on 23 Jul 2019

@author: ejimenez-ruiz
'''

import csv
from os import listdir
import os
from os.path import isfile, join

from constants import RDFS, OWL
import pandas as pd
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF
from util import utilities


#Steps
#Save header label. process
#keep map/list, index to URI property 
#create new URIS per "primary key columns"
#Assumes the left most (see column in GT?)
#Create triples for type, and for type of class
#Declare properties as DataTypeProperties or ObjectProperties
class TabularToRDF(object):
    '''
    This class converts tabular data to RDF triples. It perform a raw conversion for the OAEI, so that OAEI systems
    can participate in the Sem-Tab challenge
    '''
    
    BASE_URI = "http://www.semanticweb.org/challenge/sem-tab#"
    NAMESPACE_PREFIX = "tdkg"
    
    

    def __init__(self, target_cells_file, gt_cta_file):
        '''
        Constructor        
        '''
        
        
        
        self.main_column = dict()
        self.type_main_column = dict()
        
        #An alternative is to automatically identify the left most column with an entity mention.
        #In this particular case we know the target
        with open(target_cells_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
                        
            for row in csv_reader:
                
                if row[0] not in self.main_column or int(self.main_column[row[0]]) > int(row[1]):
                    self.main_column[row[0]] = row[1]                
                    #I think we expect one target column for entity at least in the challenge. Otherwise we keep left most
                
        with open(gt_cta_file) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
                        
            for row in csv_reader:
                #Same target column
                if row[0] in self.main_column and self.main_column[row[0]] == row[1]:
                #if self.main_column[row[0]] == row[1]:
                    self.type_main_column[row[0]] = utilities.getEntityName(row[2])
                else:
                    #self.type_main_column[row[0]] = ""
                    #print(row)
                    continue                
        
        
    
    def setUpRDFGraph(self):
        self.rdfgraph = Graph()
        self.rdfgraph.bind(TabularToRDF.NAMESPACE_PREFIX, TabularToRDF.BASE_URI)
        
        
        self.rdfgraph.add( (URIRef(TabularToRDF.BASE_URI+"table"), RDF.type, URIRef(OWL.OWLANNOTATIONPROPERTY)) )
        self.rdfgraph.add( (URIRef(TabularToRDF.BASE_URI+"column"), RDF.type, URIRef(OWL.OWLANNOTATIONPROPERTY)) )
        self.rdfgraph.add( (URIRef(TabularToRDF.BASE_URI+"row"), RDF.type, URIRef(OWL.OWLANNOTATIONPROPERTY)) )
        
        
        
        
    
    
    def saveRDFGrah(self, rdf_file_ouput):
        #output same table name as ttl
        self.rdfgraph.serialize(str(rdf_file_ouput), format='turtle')#xml,turtle
        
        #Problem with character # in file name when serializing:
        
        
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
       
        
        
        
        
        
    
    
    
    def createPropertyURIs(self, table_name, header, has_header):
        
        prop_list = list()
        
        for i in range(len(header)):
            
            p_uri = TabularToRDF.BASE_URI + "tab-" + table_name + "-col-" + str(i)
            
            prop_list.append(p_uri)
                        
            self.rdfgraph.add( (URIRef(p_uri), RDF.type, URIRef(OWL.OWLDATAPROPERTY)) )
            
            if has_header:
                self.rdfgraph.add( (URIRef(p_uri), URIRef(RDFS.LABEL), Literal(header[i])) )
            
        
        return prop_list
            
        
    def createEntity(self, table_name, row, num_row, target_column, cls_type):
        
        try:
        
            e_uri = TabularToRDF.BASE_URI  + "tab-" + table_name + "-col-" + str(target_column) + "-row-" + str(num_row)
                   
            self.rdfgraph.add( (URIRef(e_uri), RDF.type, URIRef(OWL.NAMEDINDIVIDUAL)) )
            
            self.rdfgraph.add( (URIRef(e_uri), URIRef(RDFS.LABEL), Literal(row[int(target_column)])) )
            
            self.rdfgraph.add( (URIRef(e_uri), URIRef(TabularToRDF.BASE_URI+"table"), Literal(table_name)) )
            self.rdfgraph.add( (URIRef(e_uri), URIRef(TabularToRDF.BASE_URI+"column"), Literal(target_column)) )
            self.rdfgraph.add( (URIRef(e_uri), URIRef(TabularToRDF.BASE_URI+"row"), Literal(num_row)) )
                
                
                
            if not cls_type=="":
                self.rdfgraph.add( (URIRef(self.BASE_URI+cls_type), URIRef(RDFS.LABEL), Literal(cls_type)) )
                self.rdfgraph.add( (URIRef(self.BASE_URI+cls_type), RDF.type, URIRef(OWL.OWLCLASS)) )
                self.rdfgraph.add( (URIRef(e_uri), RDF.type, URIRef(self.BASE_URI+cls_type)) )
        
        except:
            print(table_name, row, target_column)
            
        return e_uri
            
            
    
    def createRoleAssertions(self, e_uri, row, list_property_uris):
        
        #At this stage we consider all as Literals
        for i in range(len(list_property_uris)):
            if len(row[i])>0:
                self.rdfgraph.add( (URIRef(e_uri), URIRef(list_property_uris[i]), Literal(row[i])) )
            
            
    
    
    def ConvertTableToRDF(self, table_name_input, table_name, has_header, rdf_file_ouput, create_type):
        
        #Set up
        self.setUpRDFGraph()
              
        with open(table_name_input) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            if table_name in self.main_column:
                target_column = self.main_column[table_name]
            else: #End
                return
                
            if table_name in self.type_main_column:
                type_target_column = self.type_main_column[table_name]
            else:
                type_target_column=""
            
            num_row = 0;
            
            for row in csv_reader:
                
                
                
                if num_row==0: #To keep the header if any
                    
                    list_property_uris = self.createPropertyURIs(table_name, row, has_header)
                    
                    size_header = len(row)
                    
                    if has_header:
                        num_row+=1                        
                        continue
                
                
                #Wrong row
                if len(row)<size_header:
                    continue
                
                
                
                #create entity + type?
                if create_type: 
                    e_uri = self.createEntity(table_name, row, num_row, target_column, type_target_column)
                else:
                    e_uri = self.createEntity(table_name, row, num_row, target_column, "")
                
                    
                    
                
                
                
                #Create role assertions
                self.createRoleAssertions(e_uri, row, list_property_uris)
                
                
                num_row+=1
        
        
        
        #Store
        self.saveRDFGrah(rdf_file_ouput)
        
        
    def ConvertTablesToRDF(self, table_name_input, table_name, has_header, create_type):
        
        
              
        with open(table_name_input) as csv_file:
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            if table_name in self.main_column:
                target_column = self.main_column[table_name]
            else: #End
                return
                
            if table_name in self.type_main_column:
                type_target_column = self.type_main_column[table_name]
            else:
                type_target_column=""
            
            num_row = 0;
            
            for row in csv_reader:
                
                
                
                if num_row==0: #To keep the header if any
                    
                    list_property_uris = self.createPropertyURIs(table_name, row, has_header)
                    
                    size_header = len(row)
                    
                    if has_header:
                        num_row+=1                        
                        continue
                
                
                #Wrong row
                if len(row)<size_header:
                    continue
                
                
                
                #create entity + type?
                if create_type: 
                    e_uri = self.createEntity(table_name, row, num_row, target_column, type_target_column)
                else:
                    e_uri = self.createEntity(table_name, row, num_row, target_column, "")
                
                    
                    
                
                
                
                #Create role assertions
                self.createRoleAssertions(e_uri, row, list_property_uris)
                
                
                num_row+=1
        
        
        
        
        
        
        
        
    
multiple_files=False    
ch_round=1
create_type = True

#ROUND 1
if ch_round==1:    
    folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round1/"
    folder_cea_tables=folder+"CEA_Round1/"
    folder_cea_tables_rdf=folder+"CEA_RDF_tables_r1/"
    tabular2rdf = TabularToRDF(folder + "CEA_Round1_Targets.csv", folder+"CTA_Round1_gt_for_CEA.csv")
    single_rdf_file_ouput=folder + "all_tables_round1.ttl"

#ROUND 2
else:
    folder = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/"
    folder_cea_tables=folder+"Tables/"
    folder_cea_tables_rdf=folder+"CEA_RDF_tables_r2/"
    tabular2rdf = TabularToRDF(folder + "CEA_Round2_Targets.csv", folder+"CTA_Round2_GT.csv")
    single_rdf_file_ouput=folder + "all_tables_round2.ttl"


csv_file_names = [f for f in listdir(folder_cea_tables) if isfile(join(folder_cea_tables, f))]




#Set up (for only one rdf file)
if not multiple_files:
    tabular2rdf.setUpRDFGraph()

for csv_file in csv_file_names:
    
    table_name = csv_file.replace(".csv", "")
    has_header = True
    
    if multiple_files:
        rdf_file_ouput = join(folder_cea_tables_rdf, table_name) + ".ttl"
        #print(rdf_file_ouput)
        tabular2rdf.ConvertTableToRDF(join(folder_cea_tables, csv_file), table_name, has_header, rdf_file_ouput, create_type)
    else:
        tabular2rdf.ConvertTablesToRDF(join(folder_cea_tables, csv_file), table_name, has_header, create_type)

#Store (for only one rdf file)
if not multiple_files:
    tabular2rdf.saveRDFGrah(single_rdf_file_ouput)

        