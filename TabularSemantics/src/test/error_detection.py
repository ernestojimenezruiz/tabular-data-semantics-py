'''
Created on 17 Jul 2019

@author: ejimenez-ruiz
'''

import csv
from os.path import isfile, join


def detectErrorsQuotesCTA(file_cta_in, file_cta_out):
    #Remove old cases
    
    #Compute new types
    
    pass


def detectErrorsQuotesCEA(file_cea_in, file_cea_out):
    
    f_cea_out = open(file_cea_out,"w+")
    
    path_tables = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/Tables/"
    path_entities = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/"
    
    
    #tables = set()
    special_tables = set()
    
    
    #Check tables in GT
    with open(file_cea_in) as csv_file_cea:
        
        csv_reader = csv.reader(csv_file_cea)
        
        i=0
        for row in csv_reader:
            
            #Detect cases with only one row
            
            table_name = row[0]+".csv"
                
            csv_table = open(path_tables+table_name)
                
            data = [row_t for row_t in csv.reader(csv_table,  delimiter=',', quotechar='"', escapechar="\\")]
            
            try:
                data[int(row[2])][int(row[1])]
                
                column = row[1]
                
            except:
                #print(row)
                i+=1
                special_tables.add(table_name)
                
                #Get fixed column
                
                entity_mention = getEntityMention(join(path_entities, table_name), row[2])                
                
                #gets forst mention
                column= str(getColumnEntityMention(join(path_tables, table_name), entity_mention, row[2]))
                
                if row[1]!=column:
                    print(row[1] + " changed for " + column)
                else:
                    print("Problem with " + str(row))
                
            
            #Print new
            if (len(row)==3): #targets
                line_str = '\"%s\",\"%s\",\"%s\"' % (row[0], column, row[2])
            elif (len(row)==4): #gt
                line_str = '\"%s\",\"%s\",\"%s\",\"%s\"' % (row[0], column, row[2], row[3])                
            
            f_cea_out.write(line_str+'\n')
            
            
            
            #tables.add(row[0])
    
        f_cea_out.close()       
    
    
        print(i)
        print(len(special_tables))
        for t in special_tables:
            print(t)
            
            
def tablesWithErrorsQuotesCEA(file_cea_in, file_cea_out):
    
    f_cea_out = open(file_cea_out,"w+")
    
    path_tables = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/Tables/"
    path_entities = "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/WikipediaDataset/WikipediaGS/entities_instance/csv/"
    
    
    #tables = set()
    special_tables = set()
    
    
    #Check tables in GT
    with open(file_cea_in) as csv_file_cea:
        
        csv_reader = csv.reader(csv_file_cea)
        
        i=0
        for row in csv_reader:
            
            #Detect cases with only one row
            
            table_name = row[0]+".csv"
                
            csv_table = open(path_tables+table_name)
                
            data = [row_t for row_t in csv.reader(csv_table,  delimiter=',', quotechar='"', escapechar="\\")]
            
            try:
                data[int(row[2])][int(row[1])]
                
                column = row[1]
                
            except:
                #print(row)
                i+=1
                special_tables.add(table_name)
                
                #Get fixed column
                
                entity_mention = getEntityMention(join(path_entities, table_name), row[2])                
                
                #gets forst mention
                column= str(getColumnEntityMention(join(path_tables, table_name), entity_mention, row[2]))
                
                if row[1]!=column:
                    print(row[1] + " changed for " + column)
                else:
                    print("Problem with " + str(row))
                
            
            #Print new
            if (len(row)==3): #targets
                line_str = '\"%s\",\"%s\",\"%s\"' % (row[0], column, row[2])
            elif (len(row)==4): #gt
                line_str = '\"%s\",\"%s\",\"%s\",\"%s\"' % (row[0], column, row[2], row[3])                
            
            f_cea_out.write(line_str+'\n')
            
            
            
            #tables.add(row[0])
    
        f_cea_out.close()       
    
    
        print(i)
        print(len(special_tables))
        for t in special_tables:
            print(t)
       
       
       
       
def getEntityMention(file, row_id):
    csv_f = open(file)
            
    csv_reader = csv.reader(csv_f, delimiter=',', quotechar='"', escapechar="\\")
            
    for row in csv_reader:
        
        if (row[2]==row_id):
            return row[1]
        
       
               
def getColumnEntityMention(file, entity_mention, row_id):
    
    r=""
    row_count = 0
    
    csv_f = open(file)
            
    csv_reader = csv.reader(csv_f, delimiter=',', quotechar='"', escapechar="\\")
        
    n_row=0
        
    for row in csv_reader:
        #row_count+=1
        
        #print(row)
        #print(range(len(row)))
        if n_row==int(row_id):
            
            for i in range(len(row)):
                
                if row[i].replace("\"", "")==entity_mention.replace("\"", ""):
                    csv_f.close()
                    return i
            
        
        n_row+=1
            
        #r += "|".join(row)+"\n"
               
    #print(row_count)     
    #print(r)
    #print("'%s' not found in %s" % (entity_mention, file))
    
    
    csv_f.close()
    return -1       
               
               
            
    
detectErrorsQuotesCEA(
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA_error/cea_target.csv",
    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA/cea_target.csv")

#detectErrorsQuotesCEA(
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA_error/cea_gt.csv",
#    "/home/ejimenez-ruiz/Documents/ATI_AIDA/TabularSemantics/Challenge/Round2/CEA/cea_gt.csv")
    
    
    
    
    