from flask import Flask
from flask import request
from flask import jsonify
import time
import uuid

from assistant import get_answer
from db import save_conversation, save_feedback, get_recent_conversations, get_feedback_stats

app = Flask('charo-endpoint')

def print_log(message):
    print(message, flush=True)

@app.route('/conversation', methods=['POST'])
def conversation():
    user_input = request.get_json()
    print_log(user_input)
    conversation_id = str(uuid.uuid4())
    model_choice = "llama3.2:1b"
    print_log(f"New conversation started with ID: {conversation_id}")
    topic = user_input['topic']
    query = user_input["query"]
    search_type = "Vector"

    print_log(f"Getting answer from assistant using {model_choice} model and {search_type} search")
    start_time = time.time()
    answer_data = get_answer(query, topic, model_choice, search_type)
    print_log(answer_data)
    end_time = time.time()
    print_log(f"Answer received in {end_time - start_time:.2f} seconds")

    output = {
        'conversation_id': conversation_id,
        'answer': answer_data['answer']
    }

     # Save conversation to database
    print_log("Saving conversation to database")
    save_conversation(conversation_id, query, answer_data, topic)
    print_log("Conversation saved successfully")

    return jsonify(output)  ## send back the data in json format to the user

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9696)