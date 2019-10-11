'''
Created on 13 Jul 2019

@author: ejimenez-ruiz
'''
from collections import OrderedDict
import csv
from os import listdir
from os.path import isfile, join
import shutil
import sys
import time
import time

from kg.endpoints import DBpediaEndpoint
from kg.entity import KG
from matching.kg_matching import Lookup, Endpoint
from ontology.onto_access import DBpediaOntology
import pandas as pd
from util.utilities import *


def detectErrors():
    
    file_in = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells_10k.csv"
    
    with open(file_in) as csv_file:
        
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
            
            print(row[0], file=sys.stderr)
            int(row[1])
            int(row[2])
            
            


def createTargetCPA():
    
    file_in="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CPA/cpa_gt.csv"
    file_out="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CPA/cea_target.csv"
    
    
    f_out = open(file_out,"a+")
    
    
    try:                
        #Try to open with pandas. If error, then discard file
        pd.read_csv(file_in, sep=',', quotechar='"',escapechar="\\")    
        
    except:
        print("Panda error with: " + file_in)
    
    with open(file_in) as csv_file:
        
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
                
            #table, column, row_id and entity
            if len(row) < 4:
                continue
            
            
            line_str = '\"%s\",\"%s\",\"%s\"\n' % (row[0], row[1], row[2])


            f_out.write(line_str)
            
     
        f_out.close()       
    
    
    #try:                
        #Try to open with pandas. If error, then discard file
    pd.read_csv(file_out, sep=',', quotechar='"',escapechar="\\")    
        
    #except:
    #    print("Panda error with: " + file_out)
                  



def mergeFiles(files_in, file_out): 
            
    for f_in in files_in:
        addTo(f_in, file_out)



def addTo(file_in, file_out):
    
    f_out = open(file_out,"a+")
    
    
    #try:                
        #Try to open with pandas. If error, then discard file
    pd.read_csv(file_in, sep=',', quotechar='"',escapechar="\\")    
        
    #except:
    #    print("Panda error with: " + file_in)
        
    with open(file_in) as csv_file:
        
        csv_reader = csv.reader(csv_file)
        
        i=0
        for row in csv_reader:
        
            #print(i)
            i+=1
                
            #table, column, row_id and entity
            if len(row) < 2:
                continue
        
            if len(row) == 2:
                line_str = '\"%s\",\"%s\"\n' % (row[0], row[1])
            elif len(row) == 3:
                line_str = '\"%s\",\"%s\",\"%s\"\n' % (row[0], row[1], row[2])
            elif len(row) == 4:
                line_str = '\"%s\",\"%s\",\"%s\",\"%s\"\n' % (row[0], row[1], row[2], row[3].replace("\"", "%22"))
            
            f_out.write(line_str)
            
     
    f_out.close()       
    
    
    #try:                
        #Try to open with pandas. If error, then discard file
    pd.read_csv(file_out, sep=',', quotechar='"',escapechar="\\")    
        
    #except:
    #    print("Panda error with: " + file_out)
                  



def selectTablesWikipedia():
    folder_all = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/tables_instance/csv/"
    folder_r2 = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/Tables_Round2/"
    file_targets = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells_10k.csv"
    
    with open(file_targets) as csv_file:
        
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
                
            #table, column, row_id and entity
            if len(row) < 3:
                continue
            
            file_name = folder_all + row[0] + ".csv"
            
            shutil.copy2(file_name, folder_r2)
            
    

'''
base="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CEA/"
files = list()
file_in_name="cea_task_target_cells.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)


files = list()
file_in_name="gt_cea.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)


files = list()
file_in_name="gt_cea_wikiredirects.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)
'''

'''            
base="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CTA/"
files = list()
file_in_name="cta_task_target_columns.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)


files = list()
file_in_name="gt_cta.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)


files = list()
file_in_name="gt_cta_all_types.csv"
files.append(base+"0_1000/"+ file_in_name)
files.append(base+"1000_1923/"+ file_in_name)
file_out=base+file_in_name
mergeFiles(files, file_out)
'''



#detectErrors()



'''
files = list()
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells_10k.csv")
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CEA/cea_task_target_cells.csv")
file_out="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA/cea_target.csv"
mergeFiles(files, file_out)


files = list()
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_wikiredirects_10k.csv")
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CEA/gt_cea_wikiredirects.csv")
file_out="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA/cea_gt.csv"
mergeFiles(files, file_out)

'''

files = list()
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CTA_Round2/cta_task_target_columns_10k.csv")
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CTA/cta_task_target_columns.csv")
file_out="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CTA/cta_target.csv"
mergeFiles(files, file_out)


files = list()
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CTA_Round2/ground_truth_cta_all_types_10k.csv")
files.append("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/dbpbench_v8/gt/CTA/gt_cta_all_types.csv")
file_out="/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CTA/cta_gt.csv"
mergeFiles(files, file_out)


#'''



#CPA
#createTargetCPA()





#SELECT tables wikipedia. Only suing a subset of 10k from 500k
#selectTablesWikipedia()

