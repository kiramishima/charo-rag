import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from dotenv import load_dotenv
import json

from db import init_db

# load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL_LOCAL", "http://localhost:9200")
MODEL_NAME = os.getenv("MODEL_NAME", "multi-qa-MiniLM-L6-cos-v1")
INDEX_NAME = os.getenv("INDEX_NAME", "urc")
FILE_DIR = os.getenv("DOCS_DIR", "./documents")

def fetch_documents():
    print("Fetching documents...")
    docs = ['faq_idiomas.json', 'faq_requisitos.json']
    documents = []
    for doc in docs:
        with open(f"{FILE_DIR}/{doc}", "rb") as f_out:
            documents.append(json.load(f_out))
    print(f"Fetched {len(documents)} documents")
    return documents


def fetch_ground_truth():
    print("Fetching ground truth data...")
    relative_url = "ground-truth.json"
    ground_truth_url = f"{FILE_DIR}/{relative_url}"
    df_ground_truth = pd.read_json(ground_truth_url)

    ground_truth = df_ground_truth.to_dict(orient="records")
    print(f"Fetched {len(ground_truth)} ground truth records")
    return ground_truth


def load_model():
    print(f"Loading model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def setup_elasticsearch():
    print("Setting up Elasticsearch...")
    es_client = Elasticsearch(ELASTIC_URL)
    # print(es_client.info())
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "key": {"type": "keyword"},
                "document": {"type": "text"},
                "question": {"type": "text"},
                "answer": {"type": "text"} ,
                "question_text_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity":
                    "cosine"
                },
            }
        }
    }

    es_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
    es_client.indices.create(index=INDEX_NAME, body=index_settings)
    print(f"Elasticsearch index '{INDEX_NAME}' created")
    return es_client


def index_documents(es_client, documents, model):
    print("Indexing documents...")
    for item in tqdm(documents):
        for key in item.keys():
            for doc in item[key]:
                question = doc["question"]
                text = doc["answer"]
                doc["question_text_vector"] = model.encode(question + " " + text).tolist()
                print('INDEX', INDEX_NAME)
                es_client.index(index=INDEX_NAME, document=doc)
    print(f"Indexed {len(documents)} documents")


def main():
    print("Starting the indexing process...")

    documents = fetch_documents()
    ground_truth = fetch_ground_truth()
    model = load_model()
    es_client = setup_elasticsearch()
    index_documents(es_client, documents, model)

    print("Initializing database...")
    init_db()

    print("Indexing process completed successfully!")


if __name__ == "__main__":
    main()