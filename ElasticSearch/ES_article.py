import traceback
from pymongo import MongoClient
from elasticsearch import Elasticsearch

def index_map(type_name):
    
    text_mapping = {
      "type": "text",
      "fields": {
        "keyword": {
          "type": "keyword",
          "ignore_above": 256
        }
      }
    }
    
    n_gram = {
      "type": "text",
      "analyzer": "autocomplete",
      "search_analyzer": "autocomplete_search",
      "fields": {
        "keyword": {
          "type": "keyword",
          "ignore_above": 256
        }
      }
    }
    
    _index_mappings = {
      "settings": {
        "analysis": {
          "analyzer": {
            "autocomplete": {
              "tokenizer": "autocomplete",
              "filter": [
                "lowercase"
              ]
            },
            "autocomplete_search": {
              "tokenizer": "lowercase"
            }
          },
          "tokenizer": {
            "autocomplete": {
              "type": "edge_ngram",
              "min_gram": 4,
              "max_gram": 10,
              "token_chars": [
                "letter"
              ]
            }
          }
        }
      },
    "mappings": {
      type_name: {
        "properties": {
          "board": text_mapping,
          "content": n_gram,
          "tags": n_gram,
          "title": n_gram,
          "title_id": {
            "type": "long"
          },
          "title_url": text_mapping
        }
      }
    }
   }
    return _index_mappings


db = MongoClient('mongodb://127.0.0.1:27017')['forum']
collection = db.es_article
es = Elasticsearch()

if es.indices.exists(index='articles') is not True:
    es.indices.create(index='articles', body=index_map('article'))

cursor2 = collection.find({}, projection={'_id':False})

docs = [x for x in cursor2]
len(docs)

for _doc in docs:
    try:
        es.index(index='articles', doc_type='article', body=_doc)
        processed += 1
    except:
        traceback.print_exc()
