'''
Created on 19 Mar 2019

@author: ejimenez-ruiz
'''

'''
Parent lookup class
'''

import json
from pprint import pprint
import time
from urllib import parse, request

from kg.entity import KGEntity 


class Lookup(object):
    '''
    classdocs
    '''
    def __init__(self, lookup_url):
        self.service_url = lookup_url
        
        
    def getJSONRequest(self, params, attempts=3):
        
        
        try:
            #urllib has been split up in Python 3. 
            #The urllib.urlencode() function is now urllib.parse.urlencode(), 
            #and the urllib.urlopen() function is now urllib.request.urlopen().
            #url = service_url + '?' + urllib.urlencode(params)
            url = self.service_url + '?' + parse.urlencode(params)
            #print(url)
            #response = json.loads(urllib.urlopen(url).read())
            
            
            req = request.Request(url)
            #Customize headers. For example dbpedia lookup returns xml by default
            req.add_header('Accept', 'application/json')
            
            response = json.loads(request.urlopen(req).read())
            
            return response
        
        except:
            
            print("Lookup '%s' failed. Attempts: %s" % (url, str(attempts)))
            time.sleep(60) #to avoid limit of calls, sleep 60s
            attempts-=1
            if attempts>0:
                return self.getJSONRequest(params, attempts)
            else:
                return None
    
        
        
'''
DBpedia lookup access
'''
class DBpediaLookup(Lookup):
    '''
    classdocs
    
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getURL())
        
        
    def getURL(self):
        return "http://lookup.dbpedia.org/api/search/KeywordSearch"
        #TODO: prefix search allows for partial searches
        
        
        
    
    def __createParams(self, query, limit, query_cls=''):
        
        params = {
            'QueryClass' : query_cls,
            'QueryString': query,
            'MaxHits': limit,
        }
        
        return params
        
        
    def getKGName(self):
        return 'DBpedia'
    
    
    
    '''
    Returns list of ordered entities according to relevance: dbpedia
    '''
    def __extractKGEntities(self, json, filter=''):
        
        entities = list()
        
        for element in json['results']:
            
            types = set()
            
            for t in element['classes']:
                if t['uri'] != 'http://www.w3.org/2002/07/owl#Thing':
                    if t['uri'].startswith('http://dbpedia.org/ontology/') or t['uri'].startswith('http://www.wikidata.org/entity/') or t['uri'].startswith('http://schema.org/'): 
                        types.add(t['uri'])
            
            description=''
            if 'description' in element:
                description = element['description']
            
            kg_entity = KGEntity(
                element['uri'],
                element['label'],
                description,
                types,
                self.getKGName()
                )
            
            #We filter according to givem URI
            if filter=='' or element['uri']==filter:
                entities.append(kg_entity)
            #print(kg_entity)
        
        #for entity in entities:
        #    print(entity)    
        return entities
    
    
    
    def getKGEntities(self, query, limit, filter=''):        
        json = self.getJSONRequest(self.__createParams(query, limit), 3)
        
        if json==None:
            print("None results for", query)
            return list()
        
        return self.__extractKGEntities(json, filter) #Optionally filter by URI
    
    
    
    
'''
Wikidata web search API
'''
class WikidataAPI(Lookup):
    '''
    classdocs
    
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getURL())
        
        
    def getURL(self):
        return "https://www.wikidata.org/w/api.php"
    
    
    
    
    
    
    def __createParams(self, query, limit, type='item'):
        
        params = {
            'action': 'wbsearchentities',
            'format' : 'json',
            'search': query,
            'type': type,
            'limit': limit,
            'language' : 'en'
        
            
        }
        
        return params
    
    
    def getKGName(self):
        return 'Wikidata'
    
    '''
    Returns list of ordered entities according to relevance: wikidata
    '''
    def __extractKGEntities(self, json, filter=''):
        
        entities = list()
        
        for element in json['search']:
            
            #empty list of type from wikidata lookup
            types = set()
            
            description=''
            if 'description' in element:
                description = element['description']
            
            kg_entity = KGEntity(
                element['concepturi'],
                element['label'],
                description,
                types,
                self.getKGName()
                )
            
            
            #We filter according to givem URI
            if filter=='' or element['concepturi']==filter:
                entities.append(kg_entity)
            
            
            
        #for entity in entities:
        #    print(entity)    
        return entities
    
    
    
    def getKGEntities(self, query, limit, type='item', filter=''):        
        json = self.getJSONRequest(self.__createParams(query, limit, type), 3)     
        
        if json==None:
            print("None results for", query)
            return list()
           
        return self.__extractKGEntities(json, filter) #Optionally filter by URI
    
        
    
    
'''    
Entity search for Google KG
'''
class GoogleKGLookup(Lookup):
    
    
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__(self.getURL())
         
    
        self.api_key = 'AIzaSyA6Bf9yuMCCPh7vpElzrfBvE2ENCVWr-84'
        #open('.api_key').read()
    
        

        
    #def getAPIKey(self):
    #    return self.api_key

    def getURL(self):
        return 'https://kgsearch.googleapis.com/v1/entities:search'

    def __createParams(self, query, limit):
        
        params = {
            'query': query,
            'limit': limit,
            'indent': True,
            'key': self.api_key,
        }
        
        return params
    
    
    def getKGName(self):
        return 'GoogleKG'
    
    
    
    '''
    Returns list of ordered entities according to relevance: google
    '''
    def __extractKGEntities(self, json, filter=''):
        
        entities = list()
        
        for element in json['itemListElement']:
            
            types = set()
            
            for t in element['result']['@type']:
                if t != 'Thing':
                    types.add("http://schema.org/"+t)
            
            
            description=''
            if 'description' in  element['result']:
                description = element['result']['description']
            
            
            kg_entity = KGEntity(
                element['result']['@id'],
                element['result']['name'],
                description,
                types,
                self.getKGName()
                )
            
            #We filter according to givem URI
            if filter=='' or element['result']['@id']==filter:
                entities.append(kg_entity)
            #print(kg_entity)
        
        #for entity in entities:
        #    print(entity)    
        return entities
    
    
    
    def getKGEntities(self, query, limit, filter=''):    
        json = self.getJSONRequest(self.__createParams(query, limit), 3)
        
        if json==None:
            print("None results for", query)
            return list()
        
        return self.__extractKGEntities(json, filter) #Optionally filter by URI
    
    
        

if __name__ == '__main__':
    
    #query = 'Taylor Swift'
    #query = 'Scotland'
    query = "Prim's algorithm"
    query = "middle-square method"
    #query = 'http://dbpedia.org/resource/Scotland'
    query = "Israel Museum Jerusalem artist"
    #query = "ARTIC artist"
    limit=5
    
    #To be checked. Format of json seems to be different
    #kg = GoogleKGLookup()
    #entities = kg.getKGEntities(query, limit)
    #for ent in  entities:
    #    print(ent)
    
    
    dbpedia = DBpediaLookup()
    entities = dbpedia.getKGEntities(query, limit)
    print("Entities from DBPedia:")
    for ent in  entities:
        print(ent)
    
    
    print("\n")
    
    
    type="item"
    type="property"
    wikidata = WikidataAPI()
    entities = wikidata.getKGEntities(query, limit, type)
    print("Entities from Wikidata:")
    for ent in  entities:
        print(ent)
        
        