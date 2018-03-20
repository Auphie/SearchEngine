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
    },
  "_source" : {
  "excludes" : [
  "id",
  "_id",
  "page",
  "auhtor_info",
  "author_url"
  ]
 }
}
---------------------------------------------------
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
    },
  "_source" : [
  "author_name",
  "post_date",
  "title",
  "floor",
  "content"
  ]
}
