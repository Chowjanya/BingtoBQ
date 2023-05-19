import config as const
import json

import pandas as pd
from pandas import json_normalize
from datetime import date
import requests

from google.cloud import bigquery


subscription_key = const.subscription_key
endpoint = const.bing_endpoint + "v7.0/search"
#endpoint = const.bing_endpoint

#Get the Keywords from the keyword file
keywords = open(const.keywords_file, 'r').read()
keywords_list = keywords.split(',')

#Construct the https request
mkt = 'en-US'
headers = { 'Ocp-Apim-Subscription-Key': subscription_key }

columns = ["language", "displayUrl", "url", "name", "query", "date", "snippet", "rank"]
result = pd.DataFrame(columns=columns)
cols  =  ["language", "displayUrl", "url", "name", "snippet", "id"]
today = date.today()
for query in keywords_list:
    params = { 'q': query, 'mkt': mkt }
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        #For Data Exploration

        #print("\nHeaders:\n")
        #print(response.headers)
        
        #with open(query+".html", "w", encoding='utf-8') as file:
        #    file.write(str(response.json()))
        json_response = response.json()
        
        webPages = json_response['webPages']['value']
        print(type(webPages[0]))
        webSearchUrl = json_response['webPages']['webSearchUrl']
        df = json_normalize(webPages)
        my_df = df[cols]
        my_df.loc[:,"rank"] = my_df['id'].str.split('.').str[-1].astype(int)  +  1
        my_df["query"] = query
        my_df["date"] = today
        result = pd.concat([result,my_df[columns]])
    except Exception as ex:
        raise ex
result.to_csv(const.output_file,index=False)
        
#https://cloud.google.com/bigquery/docs/samples/bigquery-load-table-dataframe
# Construct a BigQuery client object.
client = bigquery.Client()
table_id = "bingtobq.BingSearch.results"

job_config = bigquery.LoadJobConfig()

#API Request
job = client.load_table_from_dataframe(result, table_id, job_config=job_config)

job.result() 

#API Request
table = client.get_table(table_id)

print("Loaded {} rows and {} columns to {}".format(table.num_rows, len(table.schema), table_id))