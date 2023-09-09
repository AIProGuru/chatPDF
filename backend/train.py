import os
import shutil
from PyPDF2 import PdfReader
import traceback
import openai
import pinecone
import csv
import os
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import re
import json
from settings import *
import docx
from database_operation.save2db import *
import speech_recognition as sr
from os import path
from pydub import AudioSegment


client = MongoClient("mongodb://localhost:27017")
db = client["gabeo"]
collection = db["billing"]

pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)


def parse_website(url):
    try:
        # Send a GET request to the website
        response = requests.get(url)
        if response.status_code == 200:
            # Extract the website content
            website_content = response.text
            soup = BeautifulSoup(website_content, "html.parser")
            # Extract the text from the parsed HTML
            extracted_text = soup.get_text()
            cleaned_text = re.sub(r"\s+", " ", extracted_text).strip()
            return cleaned_text
        else:
            print(
                f"Failed to fetch content from {url}. Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        print(traceback.format_exc())
        return False


def chunk_text(text, max_tokens, overlap_tokens):
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk.split()) + len(word.split()) > max_tokens:
            chunks.append(current_chunk)
            current_chunk = current_chunk[-overlap_tokens:] + " " + word
        else:
            current_chunk += " " + word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def parse_pdf(uploadedFile):
    try:
        pdf = PdfReader(uploadedFile)
        parsedData = {
            "num_pages": len(pdf.pages),
            "text": [page.extract_text() for page in pdf.pages],
        }
        content = []
        for pageData in parsedData["text"]:
            for each_sentence in pageData.split("\n"):
                if len(each_sentence) > 2:
                    content.append(each_sentence)
        flag = True
        if len(content) == 0:
            flag = False
        return content, flag
    except Exception as e:
        print(traceback.format_exc())
        return [], flag


def get_embedding(content, pdf_index):
    try:
        apiKey = OPENAI_KEY
        openai.api_key = apiKey
        # Embed a line of text
        response = openai.Embedding.create(
            model="text-embedding-ada-002", input=content
        )
        embedding = []
        vec_indexs = []
        # Extract the AI output embedding as a list of floats
        # embedding = response["data"][0]["embedding"]
        index = 0
        for i in response["data"]:
            index += 1
            embedding.append(i["embedding"])
            vec_indexs.append("vec" + str(index) + "-" + str(pdf_index))
        # creating the vector indexes
        return content, embedding, vec_indexs
    except Exception as e:
        print(traceback.format_exc())
        return [], [], []


def chunk_list(input_list, chunk_size):
    return [
        input_list[i : i + chunk_size] for i in range(0, len(input_list), chunk_size)
    ]


# Function for inserting embedding to pinecone


def embedding_to_pinecone(vector):
    # Initialized pinecone client
    try:
        # Testing the indexs client
        active_indexes = pinecone.list_indexes()
        print(active_indexes)
        if len(active_indexes) != 0:
            index = pinecone.Index(active_indexes[0])
            print(index)
            try:
                # inserting the embedding
                vectors_list = chunk_list(vector, 50)
                for i in vectors_list:
                    print(i)
                    index.upsert(vectors=i)
                print("Successfull inserted embeddings")
            except Exception as e:
                print("Error inserting embeddings:")
                print(traceback.format_exc())
        else:
            print("create index")
            pinecone.create_index("example-index", dimension=1536)
        return True
    except Exception as e:
        print(traceback.format_exc())
        return False


def reset_pinecone():
    try:
        active_indexes = pinecone.list_indexes()
        print(active_indexes)
        if len(active_indexes) != 0:
            index = pinecone.Index(active_indexes[0])
            # print(index.fetch(
            #     ids=["vec1-DL35016_20230630.pdf"],  namespace='pdf'))
            try:
                index.delete(deleteAll="true")
                active_indexes = pinecone.list_indexes()

                print(active_indexes)
            except Exception as e:
                print("Error reseting pinecone")
                print(traceback.format_exc())
        else:
            print("No need to reset, already empty")

    except Exception as e:
        print(traceback.format_exc())
        return False


def delete_by_id(ids):
    indexes_list = pinecone.list_indexes()
    index = pinecone.Index(indexes_list[0])
    delete_response = index.delete(ids=ids)
    print("Delete Response", delete_response)


def process_batch(batch, column_names):
    try:
        # Use the insert_many() method to insert the batch into the database
        dict_batch = [dict(zip(column_names, row)) for row in batch]

        # Use the insert_many() method to insert the batch into the database
        collection.insert_many(dict_batch, ordered=False)

        print("Processed a batch")
    except Exception as e:
        print("Error saving data to MongoDB:", str(e))
        raise e


def upserting_to_pinecone(vecs, embeddings, contents):
    indexes_list = pinecone.list_indexes()
    index = pinecone.Index(indexes_list[0])

    total_vectors = len(vecs)
    batch_size = 50

    for i in range(0, total_vectors, batch_size):
        vectors_to_upsert = []
        for j in range(i, min(i + batch_size, total_vectors)):
            vector = {
                "id": vecs[j],
                "values": embeddings[j],
                "metadata": {"content": contents[j]},
            }
            vectors_to_upsert.append(vector)

        try:
            print(vector)
            upsert_response = index.upsert(vectors=vectors_to_upsert)
            print(
                f"Upserted batch {i//batch_size + 1}/{(total_vectors+batch_size-1)//batch_size}: {upsert_response}"
            )
        except Exception as e:
            print(f"Error while upserting batch {i//batch_size + 1}: {e}")
            raise e

    print("Upsert complete")
    return 1


def train_documents(new_path):
    trained_path = "trained"  # folder with pdf files already trained
    # Get the list of file names in the folder
    file_names = os.listdir(new_path)
    # Repeat for the entire files
    data = []
    for file_name in file_names:
        content = []
        source_file = f"{new_path}/{file_name}"
        format = file_name.split(".")[-1]
        full_text = ""
        if format == "pdf":
            if is_text_based_pdf(source_file):
                full_text = extract_text_from_pdf(source_file)
            else:
                full_text = extract_text_from_image_pdf(source_file)
        elif format == "txt":
            with open(source_file, "r", encoding="utf-8") as f:
                full_text = f.read()
        elif format == "docx":
            doc = docx.Document(source_file)
            full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif format == "csv":
            import_csv(source_file)
        elif format == "xlsx":
            import_xlsx(source_file)
        elif format == "xls":
            import_xls(source_file)
        elif format == "png" or format == "jpeg" or format == "jpg":
            full_text = extract_text_from_image(source_file)
        elif (
            format == "mp4"
            or format == "mov"
            or format == "avi"
            or format == "wmv"
            or format == "mp3"
        ):
            full_text = extract_text_from_media(source_file)
        elif format == "wav":
            full_text = transcribe_wav_to_text(source_file)
        chunk_size = 1000
        overlap = 100
        chunks = [
            full_text[i : i + chunk_size]
            for i in range(0, len(full_text), chunk_size - overlap)
        ]
        print(chunks)
        try:
            sentences, embedding, vec_indexs = get_embedding(chunks, file_name)
            if len(embedding) == 0:
                print(f"Creating embedding error in {source_file}")

            output = "file_vec_info.json"
            new_data = {"file_name": file_name, "vec_indexes": vec_indexs}
            try:
                if os.path.exists(output):
                    if os.path.getsize(output) > 0:
                        with open(output, "r") as json_file:
                            data = json.load(json_file)
            except FileNotFoundError:
                data = []
            data.append(new_data)
            with open(output, "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Data added and saved to {output}")
            print(len(sentences))

            isCreatingEmbedding = upserting_to_pinecone(
                vec_indexs, embedding, sentences
            )
            if not isCreatingEmbedding:
                print("Inserting embedding error")
                return
            else:
                destination_folder = trained_path
                destination_file = os.path.join(
                    destination_folder, os.path.basename(source_file)
                )
                if os.path.exists(destination_file):
                    # If it exists, remove it
                    os.remove(destination_file)
                shutil.move(source_file, destination_folder)

        except Exception as e:
            print("Embedding error:", str(e))
            raise e


def website(url):
    content = parse_website(url)
    if content:
        max_tokens_per_chunk = 300
        overlap_tokens = 50

        chunks = chunk_text(content, max_tokens_per_chunk, overlap_tokens)
        # vector = [{"chunk": chunk} for chunk in chunks]
        sentences_list, embeddings, vec_indexs = get_embedding(chunks, url)
        print(sentences_list)

        for i in range(len(embeddings)):
            print(vec_indexs[i])
            upserting_to_pinecone(vec_indexs[i], embeddings[i], sentences_list[i])

    else:
        print("Website content parsing failed.")


# if __name__ == "__main__":
#     main()

#     # mainTXT()
#     # website("https://www.codingahead.com/cpt-code-73562-description-procedure-billing-guidelines/?expand_article=1")

#     # reset_pinecone()
