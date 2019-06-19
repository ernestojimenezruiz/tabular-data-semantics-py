'''
Created on 10 Jun 2019

@author: ejimenez-ruiz
'''
import csv
import pandas as pd

from os import listdir
from os.path import isfile, join

from matching.kg_matching import Lookup, Endpoint
from kg.entity import KG
from util.utilities import *
import time
from collections import OrderedDict
from kg.endpoints import DBpediaEndpoint
from ontology.onto_access import DBpediaOntology




def craeteCTATask(file_cea, file_cta_1, file_cta_2):
    
    dict_entities_per_col=dict()
    dict_types_per_col=dict()
    
    #We need to read from CEA file:
    #We have table, column, row_id and entity
    #We need to group entities per table-col pair
    with open(file_cea) as csv_file:
            
        csv_reader = csv.reader(csv_file)
        
        previous_key=""    
        
        for row in csv_reader:
                
            #table, column, row_id and entity
            if len(row) < 4:
                continue
    
            key = row[0] + "-col-"+ row[1]
            if previous_key!=key: #new table or column
                dict_entities_per_col[key] = set()
                previous_key = key
            
            #print(dict_entities_per_col)
            #print(key)
            dict_entities_per_col[key].add(row[3])
            
    
    #Smart lookup already combines different strategies with endpoint and other strategies
    smartlookup = Lookup()
    dbpedia_ontology = DBpediaOntology()
    dbpedia_ontology.loadOntology(True)
    
    
    
    #Get types
    for key in dict_entities_per_col:
        
        dict_types_per_col[key] = dict()
        
        for entity in dict_entities_per_col[key]:
            
            #it includes compatibility with sparql types and predicate strategy
            types_lookup = smartlookup.getTypesForEntity(entity, KG.DBpedia)
            
            #TODO
            ##get more specific types
            #check pairwise if x is sub of y
            #it may be the case that they are 2 different branches
            #Make it more optimal... if y was super class then we do not need to check it-> add it to no_leafs, leafs if survives the round
            specific_types = getMostSpecificClass(dbpedia_ontology, types_lookup)
            
            for stype in specific_types:
                
                if stype in dict_types_per_col[key]:
                    dict_types_per_col[key][stype]+=1 #voting
                else:
                    dict_types_per_col[key][stype]=1
                
    
    
    
    
    #Get most voted type per column and print file
    #File 1: single type
    #File 2: type + ancestors
    #print(dict_types_per_col)
    f_cta_1_out = open(file_cta_1,"w+")
    f_cta_2_out = open(file_cta_2,"w+")
    
    for key in dict_types_per_col:
        
        if len(dict_types_per_col[key]): #There are some types
            
            key.split("-col-")
            
            table_id = key.split("-col-")[0]
            column_id = key.split("-col-")[1]
            
            
            most_voted_type = getMostVotedType(dict_types_per_col[key])
            
            line_str = '\"%s\",\"%s\",\"%s\"' % (table_id, column_id, most_voted_type)
    
            f_cta_1_out.write(line_str+'\n')
            
            ancestors = getFilteredTypes(dbpedia_ontology.getAncestorsURIsMinusClass(dbpedia_ontology.getClassByURI(most_voted_type)), KG.DBpedia)
            
            
            for anc in ancestors:
                line_str += ',\"'+ anc + '\"'
                
            f_cta_2_out.write(line_str+'\n')
            
    
    f_cta_1_out.close()
    f_cta_2_out.close()
    
    
    
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
            #http://dbpedia.org/resource/Ahmet_%C3%96rken, Ahmet Ã\u0096rken, 1
            if len(row) < 3:
                continue
                
            entity_uri = row[0]
            row_id = row[2]
                
            entity_mention = row[1]

            column_id = getColumnEntityMention(join(folder_tables, csv_file_name), entity_mention)
                
            if column_id >= 0:
                #Output
                #“table id”, “column id”, “row id” and “DBPedia entity”
                #“9206866_1_8114610355671172497”,”0”,”121”,”http://dbpedia.org/resource/Norway”                
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





def tablesToChallengeFormat(folder_gt, folder_tables, file_out_gt, file_out_redirects_gt, file_out_gt_target, max_tables):
    
    csv_file_names = [f for f in listdir(folder_gt) if isfile(join(folder_gt, f))]
    
    
    
    
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
            
            csv_reader = csv.reader(csv_file)
            
            for row in csv_reader:
                
                #URI, text, row number
                #http://dbpedia.org/resource/Ahmet_%C3%96rken, Ahmet Ã\u0096rken, 1
                if len(row) < 3:
                    continue
                
                entity_uri = row[0]
                row_id = row[2]
                
                entity_mention = row[1]

                column_id = getColumnEntityMention(join(folder_tables, csv_file_name), entity_mention)
                
                
                entities=set()
                new_entities=set()
                
                ##Consider redirects:
                entities.update(dbpedia_ep.getWikiPageRedirect(entity_uri))
                entities.update(dbpedia_ep.getWikiPageRedirectFrom(entity_uri))
                
                for e in entities:
                    new_entities.update(dbpedia_ep.getWikiPageRedirect(e))
                    new_entities.update(dbpedia_ep.getWikiPageRedirectFrom(e))
                
                
                entities.add(entity_uri)
                entities.update(new_entities)
                
                if column_id >= 0:
                    #Output
                    #“table id”, “column id”, “row id” and “DBPedia entity”
                    #“9206866_1_8114610355671172497”,”0”,”121”,”http://dbpedia.org/resource/Norway”
                    line_str = '\"%s\",\"%s\",\"%s\"' % (table_id, column_id, row_id)                
                    f_out_target.write(line_str+'\n')
                    
                    #f_out.write('\"%s\",\"%s\",\"%s\",\"%s\"\n' % (table_id, column_id, row_id, entity_uri))
                    
                    
                    f_out.write(line_str+',\"%s\"\n' % entity_uri)
                    
                    
                    for ent in entities:
                        line_str += ',\"'+ ent + '\"'
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
            
    csv_reader = csv.reader(csv_f)
            
    for row in csv_reader:
            
        #row_count+=1
            
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
                    


#craeteCTATask("/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_10.csv",
#              "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CTA_Round2/ground_truth_cta_10.csv",
#              "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CTA_Round2/ground_truth_cta_all_types_10.csv",)

    
#tablesToChallengeFormat(
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/tables_instance/csv/",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea.csv",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells.csv"
#    )

#We need to take into account redirections if any... There may be one or more equivalent entities
tablesToChallengeFormat(
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/tables_instance/csv/",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_10k.csv",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/ground_truth_cea_wikiredirects_10k.csv",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/CEA_Round2/cea_task_target_cells_10.csv", 10)