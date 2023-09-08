import fitz  # PyMuPDF
import docx  # python-docx
import pytesseract
import os
import pandas as pd
import openpyxl  # for XLSX
from PIL import Image
import sqlite3
import csv


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
    current_dir = os.path.dirname(__file__)
    db_file = os.path.join(current_dir, "database", "database.db")
    table_name = split_filename(csv_file)  # Choose a table name for your CSV data

    conn = sqlite3.connect(db_file)

    # Read the entire CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Write the DataFrame to an SQLite database table
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def import_xlsx(xlsx_file):
    current_dir = os.path.dirname(__file__)
    db_file = os.path.join(current_dir, "database", "database.db")
    table_name = split_filename(xlsx_file)  # Choose a table name for your Excel data

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
