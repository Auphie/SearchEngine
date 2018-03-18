GET /dogforum/Breeds/_search
{
  "query" : {
  "bool": {
      "should": [
           { "match": { "title": "cocker" }},
           { "match": { "content":  "cocker"}}
        ]
    }
},
    "highlight": {
        "fields" : {
            "title" : {},
            "content" : {}
        }
    }
}
