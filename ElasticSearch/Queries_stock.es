GET /dogforum/_search
{
  "query" : {
  "bool": {
       "should": {
            "match": { "title": "cocker" }},
       "must": {
            "match": { "content":  "cocker"}}
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
# keywords can put blank!

GET /dogforum/_search
{
  "query" : {
  "bool": {
       "should": [
        {"match":{ "title": "cocker" }},
        {"match":{ "board": "pan" }}
            ],
       "must": {
            "match": { "content":  "cocker"}}
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

------------------------------------------------------
(Search by date)
GET dogforum/_search
{
    "query": {
        "range" : {
            "post_date" : {
                "gte": "01/01/2012",
                "lte": "2013",
                "format": "dd/MM/yyyy||yyyy"
            }
        }
    }
}
//  (date format can be that) "lte": "now/d",


------------------------------------------------------
(search with date range)
GET /dogforum/posts/_search
{
  "query" : {
  "bool": {
      "should": [
        {"match":{ "title": "cocker" }},
        {"match":{ "board": "pan" }}
            ],
      "must": {
            "match": { "content":  "cocker"}},
        "filter": {
          "range" : {
            "post_date" : {
                "gte": "2012-1-1",
                "lte": "2012-1-20",
                "format": "yyyy-MM-dd||yyyy"
            }
        }
    }}
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
