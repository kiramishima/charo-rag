import os
import time
import json

from openai import OpenAI

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


ELASTIC_URL = os.getenv("ELASTIC_URL", "http://localhost:9200")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")


es_client = Elasticsearch(ELASTIC_URL)
ollama_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")


def elastic_search_text(query, topic, index_name="urc"):
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "answer"],
                        "type": "best_fields",
                    }
                },
                "filter": {"term": {"topic": topic}},
            }
        },
    }

    response = es_client.search(index=index_name, body=search_query)
    return [hit["_source"] for hit in response["hits"]["hits"]]


def elastic_search_knn(field, vector, topic, index_name="urc"):
    knn = {
        "field": field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000,
        "filter": {"term": {"topic": topic}},
    }

    search_query = {
        "knn": knn,
        "_source": ["question", "answer", "key"],
    }

    es_results = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]


def build_prompt(query, search_results):
    prompt_template = """
    Eres una asistente de la Universidad Rosario Castellanos (URC), ayudas a las personas y alumnos con algunas dudas.
    Responde a la PREGUNTA con hechos basados en el CONTEXTO cuando responda a la PREGUNTA.

    PREGUNTA: {question}

    CONTEXTO:
    {context}
    """.strip()

    for doc in search_results:
        context = context + f"key: {doc['key']}\ndocument: {doc['document']}\nquestion: {doc['question']}\nanswer: {doc['answer']}\n\n"
    context = "\n\n".join(
        [
            f"key: {doc['key']}\ndocument: {doc['document']}\nquestion: {doc['question']}\nanswer: {doc['answer']}"
            for doc in search_results
        ]
    )
    return prompt_template.format(question=query, context=context).strip()


def llm(prompt, model_choice):
    start_time = time.time()
    response = ollama_client.chat.completions.create(
        model="llama3.2:1b",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    tokens = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens
    }
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return answer, tokens, response_time


def evaluate_relevance(question, answer):
    prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, 'openai/gpt-4o-mini')
    
    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except json.JSONDecodeError:
        return "UNKNOWN", "Failed to parse evaluation", tokens


def calculate_openai_cost(model_choice, tokens):
    openai_cost = 0

    if model_choice == 'openai/gpt-3.5-turbo':
        openai_cost = (tokens['prompt_tokens'] * 0.0015 + tokens['completion_tokens'] * 0.002) / 1000
    elif model_choice in ['openai/gpt-4o', 'openai/gpt-4o-mini']:
        openai_cost = (tokens['prompt_tokens'] * 0.03 + tokens['completion_tokens'] * 0.06) / 1000

    return openai_cost


def get_answer(query, course, model_choice, search_type):
    if search_type == 'Vector':
        vector = model.encode(query)
        search_results = elastic_search_knn('question_text_vector', vector, course)
    else:
        search_results = elastic_search_text(query, course)

    prompt = build_prompt(query, search_results)
    answer, tokens, response_time = llm(prompt, model_choice)

    # relevance, explanation, eval_tokens = evaluate_relevance(query, answer)

    # openai_cost = calculate_openai_cost(model_choice, tokens)

    return {
        'answer': answer,
        'response_time': response_time,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens']
    }