'''
Created on 10 Jun 2019

@author: ejimenez-ruiz
'''
from collections import OrderedDict
import csv
from os import listdir
from os.path import isfile, join
import shutil
import time
import time

from kg.endpoints import DBpediaEndpoint
from kg.entity import KG
from matching.kg_matching import Lookup, Endpoint
from ontology.onto_access import DBpediaOntology
import pandas as pd
from util.utilities import *


def craeteCTATask(file_cea, file_cta_1, file_cta_2, file_cta_target, from_table, to_table):
    
    dict_entities_per_col=dict()
    dict_types_per_col=dict()
    
    
    dict_index_types = dict()
    
    
    
    #We need to read from CEA file:
    #We have table, column, row_id and entity
    #We need to group entities per table-col pair
    with open(file_cea) as csv_file:
            
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
        
        #previous_key=""    
        
        for row in csv_reader:
            
            #table, column, row_id and entity
            if len(row) < 4:
                continue
            
            
            #if int(row[0])<=from_table or int(row[0])>to_table:
            #    continue
            
    
            key = row[0] + "-col-"+ row[1]
            #The order could be arbitrary
            #if previous_key!=key: #new table or column
            #    dict_entities_per_col[key] = set()
            #    previous_key = key
            if key not in dict_entities_per_col:
                dict_entities_per_col[key] = set()
            
            
            #print(dict_entities_per_col)
            #print(key)
            #for i in range(3,len(row)):
            #    dict_entities_per_col[key].add(row[i])
            #No need to add redirections as it is taken already into acount when extracting types
            dict_entities_per_col[key].add(row[3])
            
    
    #Smart lookup already combines different strategies with endpoint and other strategies
    smartlookup = Lookup()
    dbpedia_ontology = DBpediaOntology()
    dbpedia_ontology.loadOntology(True)
    
    
    
    #Get types
    num=0
    
    no_types=0
    
    for key in dict_entities_per_col:
        
        
        #Open files here
        #Get most voted type per column and print file
        #File 1: single type
        #File 2: type + ancestors
        #print(dict_types_per_col)
        f_cta_1_out = open(file_cta_1,"a+")
        f_cta_2_out = open(file_cta_2,"a+")
        f_cta_target = open(file_cta_target,"a+")
        
        
        
        
        dict_types_per_col[key] = dict()
        
        num+=1
        print(key + " " + str(len(dict_entities_per_col[key])) + "  -  (column " + str(num) + " out of " + str(len(dict_entities_per_col)) + ")")
        
        for entity in dict_entities_per_col[key]:
            
            #Check first if available in index
            if entity in dict_index_types:
                specific_types = dict_index_types[entity]
            else:
                #it includes compatibility with sparql types and predicate strategy
                types_lookup = smartlookup.getTypesForEntity(entity, KG.DBpedia)
                
                #TODO
                ##get more specific types
                #check pairwise if x is sub of y
                #it may be the case that they are 2 different branches
                #Make it more optimal... if y was super class then we do not need to check it-> add it to no_leafs, leafs if survives the round
                specific_types = getMostSpecificClass(dbpedia_ontology, types_lookup)
                
                dict_index_types[entity]=set()
                dict_index_types[entity].update(specific_types)
                
            
            for stype in specific_types:
                
                if stype in dict_types_per_col[key]:
                    dict_types_per_col[key][stype]+=1 #voting
                else:
                    dict_types_per_col[key][stype]=1
                
            
            
        ##Analyze specific types and votes here
        if len(dict_types_per_col[key]): #There are some types
            
            key.split("-col-")
                
            table_id = key.split("-col-")[0]
            column_id = key.split("-col-")[1]
                
                
            most_voted_type = getMostVotedType(dict_types_per_col[key])
                
            line_str = '\"%s\",\"%s\",\"%s\"' % (table_id, column_id, most_voted_type)
                
            line_str_target = '\"%s\",\"%s\"' % (table_id, column_id)
        
                
            f_cta_target.write(line_str_target+'\n')
                
            f_cta_1_out.write(line_str+'\n')
                
            cls_most_voted = dbpedia_ontology.getClassByURI(most_voted_type)
                
            if cls_most_voted==None: #safety check
                ancestors = set()
            else:
                ancestors = getFilteredTypes(dbpedia_ontology.getAncestorsURIsMinusClass(cls_most_voted), KG.DBpedia)
                
            #Store ancestors as "uri1 uri2 uri3"
            #for anc in ancestors:
            #    line_str += ',\"'+ anc + '\"'
            line_str += ',\"' + " ".join(ancestors) + '\"'
                    
            f_cta_2_out.write(line_str+'\n')
            
        else:    
            print("NO TYPES FOR "+ key)
            no_types+=1
            
    
        #We close it for each column
        f_cta_1_out.close()
        f_cta_2_out.close()
        f_cta_target.close()
    
    
    #End iteration keys (table-col)        
        
    
    
    print("Number of cases without type: "+ str(no_types))
    
    
    
    
def getMostVotedType(dictionary):
    
    max_v = -1
    most_voted=""
    for key in dictionary:
        if dictionary[key]>max_v:
            max_v=dictionary[key]
            most_voted=key

    return most_voted


def getMostSpecificClass(ontology, types):
    
    specific_classes = set()
    non_specific_classes = set()
    
    agent = "http://dbpedia.org/ontology/Agent"
    if agent in types:
        types.remove(agent)
    
    types_list = list(types)
    
    #print(types_list)
    
    
    for i in range(len(types_list)):
        
        isSubClass = True
        
        if types_list[i] in non_specific_classes:
            continue
        
        for j in range(i, len(types_list)):
            
            class_i = ontology.getClassByURI(types_list[i])
            class_j = ontology.getClassByURI(types_list[j])
            
            if class_i==None or class_j==None:
                isSubClass=False
                break
                
            
            if ontology.isSubClassOf(class_i, class_j):                
                non_specific_classes.add(types_list[j])
            
            elif ontology.isSuperClassOf(class_i, class_j):  
                non_specific_classes.add(types_list[i])
                isSubClass=False
                break
            
        #Not a superclass of others
        if isSubClass:
            specific_classes.add(types_list[i])
        
        
    #print(specific_classes)
    #for cls in specific_classes:
    #    print(getFilteredTypes(ontology.getAncestorsURIsMinusClass(ontology.getClassByURI(cls)), KG.DBpedia))
        
        
    return specific_classes




'''
Not used
'''
def tablesToChallengeFormatPandas(folder_gt, folder_tables, file_out_gt):
    
    csv_file_names = [f for f in listdir(folder_gt) if isfile(join(folder_gt, f))]
    
    f_out = open(file_out_gt,"w+")
    
    x=0
    wrong_entities=0
    
    for csv_file_name in csv_file_names: 
        
        #print(csv_file_name)
        
        table_id = csv_file_name.replace(".csv", "")
        
        csv_file = pd.read_csv(join(folder_gt, csv_file_name), sep=',', quotechar='"',escapechar="\\")    
        df = csv.reader(csv_file)
        
        for row in df:
        
            #URI, text, row number
            #http://dbpedia.org/resource/Ahmet_%C3%96rken, Ahmet A\u0096rken, 1
            if len(row) < 3:
                continue
                
            entity_uri = row[0]
            row_id = row[2]
                
            entity_mention = row[1]

            column_id = getColumnEntityMention(join(folder_tables, csv_file_name), entity_mention)
                
            if column_id >= 0:
                #Output
                #table id, column id, row id and DBPedia entity
                #9206866_1_8114610355671172497,0,121,http://dbpedia.org/resource/Norway                
                #f_out.write('\"%s\",\"%s\",\"%s\",\"%s\"\n' % (table_id, column_id, row_id, entity_uri))
                writer = csv.writer(f_out, quoting=csv.QUOTE_ALL)
                writer.writerow([table_id, column_id, row_id, entity_uri])
                    
                
                    
                print('\"%s\",\"%s\",\"%s\",\"%s\"' % (table_id, column_id, row_id, entity_uri))
            else:
                wrong_entities+=1
                    
        #if x > 20000:        
        #    break   
        #x+=1
        
        del df
        
        
    print("Wrong entities: %d" % wrong_entities)
    writer.close()    
    f_out.close()





def extensionWithWikiRedirects(file_gt, folder_tables, file_out_gt, file_out_redirects_gt, file_out_gt_target, max_rows):
    #print(csv_file_name)
        
    f_out = open(file_out_gt,"a+")
    f_out_redirects = open(file_out_redirects_gt,"a+")
    f_out_target = open(file_out_gt_target,"a+")
    
    n_rows=0
    panda_errors = 0
    
    dbpedia_ep = DBpediaEndpoint()
        
    table_id = ""
        
    dict_entities = dict()
    
    #READ CURRENT CACHE
    #init dict_entities with current state of file_out_redirects_gt
    with open(file_out_redirects_gt) as csv_file_redirections:
        
        csv_reader = csv.reader(csv_file_redirections, delimiter=',', quotechar='"', escapechar="\\")
        
        #"1","0","1","http://dbpedia.org/resource/Uno_Von_Troil http://dbpedia.org/resource/Uno_von_Troil"
        for row in csv_reader:
            
            entity_list = row[3].split(" ")
            
            for e in entity_list:
                
                if e not in dict_entities:                    
                    dict_entities[e] = set(entity_list)
            
            
        
        
        
    with open(file_gt) as csv_file:
                
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
        for row in csv_reader:
                
            #file, col, row, URI
            #note that in Okties GT it is given file, row, col 
            #1,1,0,http://dbpedia.org/resource/Uno_von_Troil
            
            if len(row) < 4:
                continue
            
            
            #entity_uri = row[3]    
            entity_uri = row[3].replace("\"", "%22")
            
            #To avoid cases from "http://sws.geonames.org/"
            #if entity_uri.startswith("http://sws.geonames.org/"):
            same_as_resources = set()
            if not entity_uri.startswith("http://dbpedia.org/resource/"):
                #print(getFilteredResources(dbpedia_ep.getSameEntities(entity_uri), KG.DBpedia))
                same_as_resources = getFilteredResources(dbpedia_ep.getSameEntities(entity_uri), KG.DBpedia)                
                #print(row[0])
                #print(row[1])
                #print(row[2])                               
                #print(entity_uri)
                
                if len(same_as_resources)==0:
                    print("No dbpedia entity for: %s, %s, %s, %s" % (row[0], row[1], row[2], entity_uri) )                    
                else:
                    #We keep only one of the same_as dbpedia resoruces
                    for r in same_as_resources:
                        entity_uri = r
                    
                    ##We will consider other same as later
                    same_as_resources.remove(entity_uri)
                    
                #break
            
            entity_uri = row[3].replace("\"", "%22")
            
            
            #if int(row[0])<1000: #Jiaoyan starts from table file 1,000            
            #if int(row[0])>=1000: #ernesto
            #if int(row[0])>=3: #ernesto 
            #if int(row[0])<587 or int(row[0])>=1000:  
            #    continue
            
            if not table_id==row[0]:
                
                #Change of table we close and then reopen again to keep a better storage of intermediate points
                f_out.close()
                f_out_redirects.close()
                f_out_target.close() 
                
                
                table_id = row[0]
                print(table_id)
                
                
                f_out = open(file_out_gt,"a+")
                f_out_redirects = open(file_out_redirects_gt,"a+")
                f_out_target = open(file_out_gt_target,"a+")
                
                
                
            col_id = row[2]#Reverse according to input
            row_id = row[1]
                
            csv_file_name = table_id + ".csv"
            
            try:                
                #Try to open with pandas. If error, then discard file
                pd.read_csv(join(folder_tables, csv_file_name), sep=',', quotechar='"',escapechar="\\")    
                #df = csv.reader(csv_file)
            except:
                panda_errors+=1
                continue
            
            
            entities=set()
            
            ##Keep and index to avoid unnecessary queries
            if entity_uri in dict_entities:
                entities.update(dict_entities[entity_uri])
            else:
                #entities=set()
                new_entities=set()
                    
                ##Consider redirects:
                entities.update(dbpedia_ep.getWikiPageRedirect(entity_uri))
                entities.update(dbpedia_ep.getWikiPageRedirectFrom(entity_uri))
                entities.update(same_as_resources) #in case there were more than one
                
                                                
                #two iterations    
                for e in entities:
                    new_entities.update(dbpedia_ep.getWikiPageRedirect(e))
                    new_entities.update(dbpedia_ep.getWikiPageRedirectFrom(e))
                    
                
                entities.add(entity_uri)
                entities.update(new_entities)
                
                
                dict_entities[entity_uri] = set()
                dict_entities[entity_uri].update(entities)
            
                
            #Output
            #table id, column id, row id and DBPedia entity
            #9206866_1_8114610355671172497,0,121,http://dbpedia.org/resource/Norway
            line_str = '\"%s\",\"%s\",\"%s\"' % (table_id, col_id, row_id)                
            f_out_target.write(line_str+'\n')
                    
            #f_out.write('\"%s\",\"%s\",\"%s\",\"%s\"\n' % (table_id, column_id, row_id, entity_uri))
                    
            f_out.write(line_str+',\"%s\"\n' % entity_uri)
                    
                    
            #for ent in entities:
            #    line_str += ',\"'+ ent + '\"'
            line_str += ',\"' + " ".join(entities) + '\"'
                    
            f_out_redirects.write(line_str+'\n')
                    
            
        
            ##Number of rows
            if n_rows > max_rows: #200000        
                break   
            n_rows+=1
        
        
        
    print("Panda errors: %d" % panda_errors)    
    f_out.close()
    f_out_redirects.close()
    f_out_target.close()
    
    
    


def tablesToChallengeFormat(folder_gt, folder_tables, file_out_gt, file_out_redirects_gt, file_out_gt_target, max_tables):
    
    #csv_file_names = [f for f in listdir(folder_gt) if isfile(join(folder_gt, f))]
    
    csv_file_names = []
    csv_file_names.append("2014_Tour_of_Turkey#6.csv")
    
    
    
    
    f_out = open(file_out_gt,"w+")
    f_out_redirects = open(file_out_redirects_gt,"w+")
    f_out_target = open(file_out_gt_target,"w+")
    
    n_tables=0
    wrong_entities=0
    panda_errors = 0
    
    
    dbpedia_ep = DBpediaEndpoint()
    
    for csv_file_name in csv_file_names: 
        
        #print(csv_file_name)
        
        with open(join(folder_gt, csv_file_name)) as csv_file:
            
            try:                
                #Try to open with pandas. If error, then discard file
                pd.read_csv(join(folder_tables, csv_file_name), sep=',', quotechar='"',escapechar="\\")    
                #df = csv.reader(csv_file)
            except:
                panda_errors+=1
                continue

            
            
            table_id = csv_file_name.replace(".csv", "")
            
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
            
            for row in csv_reader:
                
                #URI, text, row number
                #http://dbpedia.org/resource/Ahmet_%C3%96rken, Ahmet A\u0096rken, 1
                if len(row) < 3:
                    continue
                
                entity_uri = row[0]
                row_id = row[2]
                
                entity_mention = row[1]

                column_id = getColumnEntityMention(join(folder_tables, csv_file_name), entity_mention)
                
                
                entities=set()
                new_entities=set()
                
                ##Consider redirects:
                #entities.update(dbpedia_ep.getWikiPageRedirect(entity_uri))
                #entities.update(dbpedia_ep.getWikiPageRedirectFrom(entity_uri))
                
                #for e in entities:
                #    new_entities.update(dbpedia_ep.getWikiPageRedirect(e))
                #    new_entities.update(dbpedia_ep.getWikiPageRedirectFrom(e))
                
                
                entities.add(entity_uri)
                #entities.update(new_entities)
                
                if column_id >= 0:
                    #Output
                    #table id,column id, row id and DBPedia entity
                    #9206866_1_8114610355671172497,0,121,http://dbpedia.org/resource/Norway
                    line_str = '\"%s\",\"%s\",\"%s\"' % (table_id, column_id, row_id)                
                    f_out_target.write(line_str+'\n')
                    
                    #f_out.write('\"%s\",\"%s\",\"%s\",\"%s\"\n' % (table_id, column_id, row_id, entity_uri))
                    
                    
                    f_out.write(line_str+',\"%s\"\n' % entity_uri)
                    
                    
                    #for ent in entities:
                    #    line_str += ',\"'+ ent + '\"'
                    line_str += ',\"' + " ".join(entities) + '\"'
                    
                    f_out_redirects.write(line_str+'\n')
                    
                    
                    
                    #TODO 
                    #Read with pandas: https://www.datacamp.com/community/tutorials/pandas-read-csv
                    #There are some errors with "\"
                    #writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                    #writer.writerow()
                    
                    #print('\"%s\",\"%s\",\"%s\",\"%s\"' % (table_id, column_id, row_id, entity_uri))
                else:
                    wrong_entities+=1
        
        ##Small dataset with only approx. 20k tables out of >400k
        if n_tables > max_tables: #200000        
            break   
        n_tables+=1
        
    print("Panda errors: %d" % panda_errors)    
    print("Wrong entities: %d" % wrong_entities)    
    f_out.close()
    f_out_redirects.close()
    f_out_target.close()
    
        
        


'''
Not used
'''
def getColumnEntityMentionPandas(file, entity_mention):
    
    r=""
    row_count = 0
    
    csv_file = pd.read_csv(file, sep=',', quotechar='"',escapechar="\\")    
    df = csv.reader(csv_file)
    
    
            
    for row in df:
            
        #row_count+=1
            
      
            
        for i in range(len(row)):
            
            if row[i].replace("\"", "")==entity_mention.replace("\"", ""):
                del df
                return i
        
        r += "|".join(row)+"\n"
               
    #print(row_count)     
    #print(r)
    print("'%s' not found in %s" % (entity_mention, file))    
    del df
    return -1


    
def getColumnEntityMention(file, entity_mention):
    
    r=""
    row_count = 0
    
    csv_f = open(file)
            
    csv_reader = csv.reader(csv_f, delimiter=',', quotechar='"', escapechar="\\")
            
    for row in csv_reader:
            
        #row_count+=1
        
        print(row)
        print(range(len(row)))
        
            
        for i in range(len(row)):
            if row[i].replace("\"", "")==entity_mention.replace("\"", ""):
                csv_f.close()
                return i
        
        #r += "|".join(row)+"\n"
               
    #print(row_count)     
    #print(r)
    #print("'%s' not found in %s" % (entity_mention, file))
    
    
    csv_f.close()
    return -1
          
          
          
#To create a single filed with entities: "uri1 uri2 uri3"
def modifyCEATask(file_cea, file_cea_out): 
            
    with open(file_cea) as csv_file:
        
        f_cea_out = open(file_cea_out,"w+")
        
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"', escapechar="\\")
        
        for row in csv_reader:
                
            #table, column, row_id and entity
            if len(row) < 4:
                continue
            
            entities = set()
            
            for i in range(3,len(row)):
                entities.add(row[i])
            
            
            line_str = '\"%s\",\"%s\",\"%s\"' % (row[0], row[1], row[2])                
            
                    
            line_str += ',\"' + " ".join(entities) + '\"'
                    
            f_cea_out.write(line_str+'\n')
            
     
        f_cea_out.close()       
            



         

start_time = time.time()            
                    
#myList = ['a','b','c','d']
#myList = list()
#myString = " ".join(myList)
#print('"'+myString+'"')

#To have only 4 fiels instead of many depending on the number of GT entities
#modifyCEATask(
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_wikiredirects_10k_2.csv",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_wikiredirects_10k.csv")




#JIAOYAN: to be changed with your path
#You may need to create folders CEA and CTA inside gt
#base = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Round3/"
base = "/home/ernesto/Documents/Sem-Tab/Round4/"
####CTA
#'''
craeteCTATask(base+"gt/CEA/gt_cea.csv",
              base+"gt/CTA/gt_cta.csv",
              base+"gt/CTA/gt_cta_all_types.csv",
              base+"gt/CTA/cta_task_target_columns.csv", 0, 3000) #jiaoyan
#'''



'''
base= "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round1/"

craeteCTATask(base+"CEA_Round1_gt.csv",
              base+"CTA_Round1_gt_for_CEA.csv",
              base+"CTA_Round1_gt_for_CEA_all_types.gt",
              base+"CTA_Round1_targets_for_CEA.csv", 0, 3000)
'''

####CEA
'''
extensionWithWikiRedirects(
    base+"gt/cea_gt.csv",
    base+"tables/",
    base+"gt/CEA/gt_cea.csv",
    base+"gt/CEA/gt_cea_wikiredirects.csv",
    base+"gt/CEA/cea_task_target_cells.csv", 500000) #Max < 400,000
'''





#tablesToChallengeFormat(
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/tables_instance/csv/",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea.csv",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells.csv"
#    )

#We need to take into account redirections if any... There may be one or more equivalent entities
'''
tablesToChallengeFormat(
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/tables_instance/csv/",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_x.csv",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_wikiredirects_x.csv",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells_x.csv", 1)
'''






elapsed_time = time.time() - start_time
print("Time: " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
    

    
