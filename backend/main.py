from flask import Flask, request, jsonify, Response
from langchain import OpenAI, SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_experimental.sql.base import SQLDatabaseSequentialChain
import os
import openai
import traceback
import pinecone
from flask_cors import CORS
from settings import *
from flask import Flask, send_from_directory
import ast
import re
import sqlite3
from langchain.prompts.prompt import PromptTemplate
import json
from train import *

import time

app = Flask(__name__, static_folder="../chatpdf/build/static")
CORS(app)

key = PINECONE_API_KEY
env_value = PINECONE_ENV
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

try:
    pinecone.init(api_key=key, environment=env_value)
    activate_indexs = pinecone.list_indexes()
    PINECONE_INDEX = pinecone.Index(activate_indexs[0])
    openai.api_key = OPENAI_KEY

except Exception as e:
    raise e


@app.route("/")
def index():
    return send_from_directory("../chatpdf/build", "index.html")


@app.route("/<path:text>")
def all_routes(text):
    return send_from_directory("../chatpdf/build", "index.html")


previous_questions_and_answers = []


def find_in_pdf(query):
    # queryResponse = query_embedding(query, "pdf")
    new_question = query
    errors = get_moderation(new_question)
    if errors:
        return {
            "type": "generic",
            "content": "Sorry, your question didn't pass the moderation check",
        }

    queryResponse = query_pinecone(query)

    if not queryResponse:
        return jsonify({"message": "Querying to pinecone Error"})
    inputSentence = ""
    ids = ""
    for i in queryResponse["matches"]:
        inputSentence += i["metadata"]["content"]
        ids += i["id"]
    inputSentence = limit_string_tokens(inputSentence, 1000)
    print(ids)
    try:
        # prompt = f"""
        #             I want you to act as an accountant and come up with creative ways to manage finances.
        #             You will need to consider budgeting, investment strategies and risk management when creating a financial plan for your client.
        #             In some case, you may also need to provide advice on taxation laws and regulations in order to help them maximize their profits.
        #             My first suggestion request is "Create a financial plan for a small business that focuses on cost savings and long-term investments"
        #             You have to use User's language, so for example, if the user asks you something in Dutch, you need to answer in Dutch.
        #             You are only a language model, so don't pretend to be a human.
        #             Use the next Context to generate answer about user query. If the Context has no relation to user query, you need to generate answer based on the knowledge that you know.
        #             And don't mention about the given Context. It is just a reference.
        #             Context: {inputSentence}
        #             query: {query}

        # """

        prompt = f"""
                    Seeking guidance from experienced staff with expertise on financial markets, incorporating factors such as inflation rate or return estimates along with tracking stock prices over lengthy period ultimately helping customer understand sector then suggesting safest possible options available where he/she can allocate funds depending upon their requirement and interests!
                    Starting query - "What currently is best way to invest money short term prospective?"
                    You have to use User's language, so for example, if the user asks you something in Dutch, you need to answer in Dutch.
                    User trains you by uploading document and ask question. Then you need to findout appropriate answer from the Context.
                    The next context is from the data user uploaded before so please refer that to generate response about the user query.
                    And if the query and Context has any relation, you must generate some valuable response, don't say like - I don't have access to specific documents - because user already uploaded the documents.
                    If the Context has no relation to user query, you need to answer like Sorry I don't have such information.
                    And don't mention about the given Context. It is just a reference.
                    Context: {inputSentence}
                    query: {query}

        """
        response = get_response(prompt, previous_questions_and_answers, new_question)
        previous_questions_and_answers.append((new_question, response))
        return {"type": "generic", "content": response}

    except Exception as e:
        print(traceback.format_exc())
        return "Net Error"


@app.route("/update_pdf/", methods=["POST", "GET"])
def update_pdf():
    if request.method == "POST":
        file_name = request.form["oldFileName"]
        with open("file_vec_info.json", "r") as file:
            data = json.load(file)
        ids = get_ids_from_file_name(file_name, data)
        delete_by_id(ids)
        remove_item_by_file_name(file_name, data)

        file_path = f"trained/{file_name}"  # Replace with the path of the file you want to delete
        try:
            os.remove(file_path)
            print(f"{file_path} has been successfully deleted.")
        except OSError as e:
            print(f"Error deleting {file_path}: {e}")
        return {"status": "success"}


def get_ids_from_file_name(file_name, data):
    vec_ids = []
    for item in data:
        if item["file_name"] == file_name:
            vec_ids.extend(item["vec_indexes"])
    return vec_ids


def remove_item_by_file_name(file_name, data):
    updated_data = [item for item in data if item["file_name"] != file_name]
    with open("file_vec_info.json", "w") as file:
        json.dump(updated_data, file, indent=4)


@app.route("/upload_documents/", methods=["POST", "GET"])
def upload_documents():
    if request.method == "POST":
        # Check if the POST request has a file part
        len = int(request.form["length"])
        if len == 0:
            return "No file part"

        for i in range(len):
            document_file = request.files[f"file-{i}"]

            # Ensure the uploads folder exists, create it if necessary
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])

            # Save the uploaded PDF file to the uploads folder
            document_file.save(
                os.path.join(app.config["UPLOAD_FOLDER"], document_file.filename)
            )

            # Optionally, you can perform further processing on the uploaded PDF file here

        train_documents(app.config["UPLOAD_FOLDER"])

        return {"status": "success"}


@app.route("/query_pdf/", methods=["POST", "GET"])
def chatPDF():
    if request.method == "POST":
        query = request.form["query"]
        response = find_in_pdf(query)
        return response


def get_moderation(question):
    """
    Check the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        {"role": "system", "content": instructions},
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-10:]:
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
    # add the new question
    messages.append({"role": "user", "content": new_question})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )
    return completion.choices[0].message.content


def generate_text(openAI_key, prompt, engine="text-davinci-003"):
    speed = 0.05
    openai.api_key = openAI_key
    completions = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.1,
        seed=123,
        # stream=True,
    )
    return completions["choices"][0]["text"]
    # for event in completions:
    #     event_text = event["choices"][0]["text"]
    #     yield event_text


def limit_string_tokens(string, max_tokens):
    tokens = string.split()  # Split the string into tokens
    if len(tokens) <= max_tokens:
        return string  # Return the original string if it has fewer or equal tokens than the limit

    # Join the first 'max_tokens' tokens and add an ellipsis at the end
    limited_string = " ".join(tokens[:max_tokens])
    return limited_string


def creating_embedding(query):
    api_key = OPENAI_KEY
    try:
        openai.api_key = api_key

        res = openai.Embedding.create(model="text-embedding-ada-002", input=[query])

        embedding = res["data"][0]["embedding"]

        return embedding

    except Exception as e:
        print(traceback.format_exc())

        return []


def query_pinecone(query):
    sentences, embeddings, vec_indexes = get_embedding([query])
    if len(embeddings) == 0:
        return jsonify({"message": "Creating Embedding Error"})
    try:
        query_res = PINECONE_INDEX.query(
            top_k=5,
            include_values=True,
            include_metadata=True,
            vector=embeddings[0],
        )
        return query_res
        # grouped_sentences = {}
        # for result in query_res['matches']:
        #     vector_id = result['id']
        #     file_name = re.search(r"vec\d+-(.+)\.pdf", vector_id).group(1)
        #     print(file_name)
        #     if file_name not in grouped_sentences:
        #         grouped_sentences[file_name] = []
        #     grouped_sentences[file_name].append(result['metadata']['sentence'])

        # return grouped_sentences

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"message": "Error in Pinecone"})


def get_embedding(content):
    try:
        apiKey = OPENAI_KEY
        openai.api_key = apiKey
        response = openai.Embedding.create(
            model="text-embedding-ada-002", input=content
        )
        embedding = []
        vec_indexes = []
        index = 0
        for i in response["data"]:
            index += 1
            embedding.append(i["embedding"])
            vec_indexes.append("vec" + str(index))
        return content, embedding, vec_indexes
    except Exception as e:
        print(traceback.format_exc())
        return [], [], []


if __name__ == "__main__":
    app.run(debug=True)
