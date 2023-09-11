import fitz  # PyMuPDF
import docx  # python-docx
import pytesseract
import os
import pandas as pd
import openpyxl  # for XLSX
from PIL import Image
import sqlite3
import csv
import moviepy.editor as mp
import speech_recognition as sr
from pydub import AudioSegment


# Function to transcribe a WAV file to text
def transcribe_wav_to_text(wav_file):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio = r.record(source)  # read the entire audio file
        full_text = r.recognize_google(audio)
        return full_text
    except sr.UnknownValueError as uv:
        raise uv
    except sr.RequestError as e:
        raise e


# Function to convert various media formats to WAV if needed
def convert_media_to_wav(source_file, output_wav_file):
    _, file_extension = os.path.splitext(source_file)
    # Check if the source file is already in WAV format
    if file_extension.lower() == ".wav":
        # No conversion needed, just copy the source to the output file
        os.rename(source_file, output_wav_file)
    else:
        # Convert the source file to WAV
        if file_extension.lower() in (".mp4", ".avi", ".mov", ".wmv"):
            video = mp.VideoFileClip(source_file)
            audio_file = video.audio
            audio_file.write_audiofile(output_wav_file)
            # Close the video and audio objects to release resources
            video.close()
            audio_file.close()
        elif file_extension.lower() == ".mp3":
            sound = AudioSegment.from_mp3(source_file)
            sound.export(output_wav_file, format="wav")
            # Close the audio object to release resources
            sound.close()
        else:
            raise ValueError("Unsupported file format")


# Function to extract text from various media formats
def extract_text_from_media(source_file):
    # Define temporary WAV file path
    temp_wav_file = "temp.wav"

    # Convert the source file to WAV if needed
    convert_media_to_wav(source_file, temp_wav_file)

    # Transcribe the WAV file to text
    text = transcribe_wav_to_text(temp_wav_file)

    # Clean up the temporary WAV file
    os.remove(temp_wav_file)

    return text


def extract_text_from_pdf(pdf_file):
    try:
        pdf_document = fitz.open(pdf_file)
        extracted_text = ""

        for page_number in range(pdf_document.page_count):
            page = pdf_document.load_page(page_number)
            text = page.get_text()
            extracted_text += text

        pdf_document.close()
        return extracted_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def is_text_based_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            # If any page contains text, it's a text-based PDF
            if text:
                return True
        # If no text found in any page, it's likely an image-based PDF
        return False
    except Exception as e:
        # Handle exceptions (e.g., invalid PDF format)
        print(f"Error: {e}")
        return False


def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        extracted_text = ""

        for paragraph in doc.paragraphs:
            extracted_text += paragraph.text + "\n"

        return extracted_text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_text_from_image_pdf(pdf_file):
    try:
        extracted_text = ""
        pages = fitz.open(pdf_file)

        for page_number in range(len(pages)):
            image_page = pages.load_page(page_number)
            image = image_page.get_pixmap()
            image_file = f"temp_image_page_{page_number}.png"
            image.save(image_file)

            image_text = pytesseract.image_to_string(image_file)
            extracted_text += image_text

            os.remove(image_file)  # Remove the temporary image file

        return extracted_text
    except Exception as e:
        print(f"Error extracting text from image-based PDF: {e}")
        return ""


def extract_text_from_image(img_file):
    image = Image.open(img_file)
    text = pytesseract.image_to_string(image)
    return text


def import_csv(csv_file):
    # Extract the filename from the path
    file_name = os.path.basename(csv_file)

    current_dir = os.path.dirname(__file__)
    db_file = os.path.join(current_dir, "database", "database.db")

    # Use the filename (without extension) as the table name
    table_name = os.path.splitext(file_name)[0]

    conn = sqlite3.connect(db_file)

    # Read the entire CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Write the DataFrame to an SQLite database table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def import_xlsx(xlsx_file):
    file_name = os.path.basename(xlsx_file)
    current_dir = os.path.dirname(__file__)
    db_file = os.path.join(current_dir, "database", "database.db")
    table_name = os.path.splitext(file_name)[0]

    conn = sqlite3.connect(db_file)

    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(xlsx_file)

    # Write the DataFrame to an SQLite database table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def import_xls(xls_file):
    current_dir = os.path.dirname(__file__)
    db_file = os.path.join(current_dir, "database", "database.db")
    table_name = split_filename(xls_file)  # Choose a table name for your Excel data

    conn = sqlite3.connect(db_file)

    # Read the XLS file into a pandas DataFrame
    df = pd.read_excel(xls_file, engine="xlrd")

    # Write the DataFrame to an SQLite database table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def split_filename(filename):
    name, extension = os.path.splitext(filename)
    return name
