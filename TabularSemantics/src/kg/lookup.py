'''
Created on 19 Mar 2019

@author: ejimenez-ruiz
'''

import json
from urllib import parse,request
from pprint import pprint
from kg.entity import KGEntity 



'''
Parent lookup class
'''
class Lookup(object):
    '''
    classdocs
    '''
    def __init__(self, lookup_url):
        self.service_url = lookup_url
        
        
    def getJSONRequest(self, params):
        
        #urllib has been split up in Python 3. 
        #The urllib.urlencode() function is now urllib.parse.urlencode(), 
        #and the urllib.urlopen() function is now urllib.request.urlopen().
        #url = service_url + '?' + urllib.urlencode(params)
        url = self.service_url + '?' + parse.urlencode(params)
        print(url)
        #response = json.loads(urllib.urlopen(url).read())
        
        
        req = request.Request(url)
        #Customize headers. For example dbpedia lookup returns xml by default
        req.add_header('Accept', 'application/json')
        
        
        response = json.loads(request.urlopen(req).read())
        
        return response
    
        
       
        
        
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
        
        
        
    
    def createParams(self, query, limit, query_cls=''):
        
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
    def extractKGEntities(self, json):
        
        entities = list()
        
        for element in json['results']:
            
            types = set()
            
            for t in element['classes']:
                if t['uri'] != 'http://www.w3.org/2002/07/owl#Thing':
                    if t['uri'].startswith('http://dbpedia.org/ontology/') or t['uri'].startswith('http://www.wikidata.org/entity/') or t['uri'].startswith('http://schema.org/'): 
                        types.add(t['uri'])
            
            kg_entity = KGEntity(
                element['uri'],
                element['label'],
                element['description'],
                types,
                self.getKGName()
                )
            
            entities.append(kg_entity)
            #print(kg_entity)
        
        #for entity in entities:
        #    print(entity)    
        return entities
    
    
    
    
    
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
    
    
    
    
    
    
    def createParams(self, query, limit):
        
        params = {
            'action': 'wbsearchentities',
            'format' : 'json',
            'search': query,
            'limit': limit,
            'language' : 'en'
            
        }
        
        return params
    
    
    def getKGName(self):
        return 'Wikidata'
    
    '''
    Returns list of ordered entities according to relevance: wikidata
    '''
    def extractKGEntities(self, json):
        
        entities = list()
        
        for element in json['search']:
            
            #empty list of type from wikidata lookup
            types = set()
            
            kg_entity = KGEntity(
                element['concepturi'],
                element['label'],
                element['description'],
                types,
                self.getKGName()
                )
            
            entities.append(kg_entity)
            
        #for entity in entities:
        #    print(entity)    
        return entities
        
    
    
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

    def createParams(self, query, limit):
        
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
    def extractKGEntities(self, json):
        
        entities = list()
        
        for element in json['itemListElement']:
            
            types = set()
            
            for t in element['result']['@type']:
                if t != 'Thing':
                    types.add("http://schema.org/"+t)
            
            kg_entity = KGEntity(
                element['result']['@id'],
                element['result']['name'],
                element['result']['description'],
                types,
                self.getKGName()
                )
            
            entities.append(kg_entity)
            #print(kg_entity)
        
        #for entity in entities:
        #    print(entity)    
        return entities
        

if __name__ == '__main__':
    
    #query = 'Taylor Swift'
    query = 'Scotland'
    limit=5
    
    kg = GoogleKGLookup()
    
    json1 = kg.getJSONRequest(kg.createParams(query, limit))
    #pprint(json1)    
    kg.extractKGEntities(json1)
    
    
    
    
    
    dbpedia = DBpediaLookup()
    json1 = dbpedia.getJSONRequest(dbpedia.createParams(query, limit))
    #pprint(json1)   
    dbpedia.extractKGEntities(json1) 
    
    
    
    
    wikidata = WikidataAPI()
    json1 = wikidata.getJSONRequest(wikidata.createParams(query, limit))
    #pprint(json1)
    wikidata.extractKGEntities(json1)
    