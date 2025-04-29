from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from io import BytesIO
import streamlit as st
from streamlit_tags import st_tags_sidebar
import json
import html2text
from bs4 import BeautifulSoup
from typing import List, Type
from pydantic import BaseModel, create_model
import tiktoken
from datetime import datetime
import re
import pandas as pd
import google.generativeai as genai
from src.assets import USER_AGENTS,SYSTEM_MESSAGE,USER_MESSAGE

# Function to initialize the WebDriver
def init_driver():  
    options = EdgeOptions()
    options.use_chromium = True
    service = EdgeService() #executable_path=r'C:\Users\Anant_Jain\OneDrive\Desktop\Infosys Springboard\Tasks\msedgedriver.exe'
    driver = webdriver.Edge(service=service, options=options)
    return driver

# Function to fetch HTML using Selenium
def fetch_html_selenium(url, attended_mode=False, driver=None):
    if driver is None:
        driver = init_driver()
        should_quit = True
        if not attended_mode:
            driver.get(url)
    else:
        should_quit = False
        if not attended_mode:
            driver.get(url)

    try:
        if not attended_mode:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(random.uniform(1.1, 1.8))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1.2);")
            time.sleep(random.uniform(1.1, 1.8))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1);")
            time.sleep(random.uniform(1.1, 1.8))
        html = driver.page_source
        return html
    finally:
        if should_quit:
            driver.quit()

# Clean HTML content by removing headers and footers
def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for element in soup.find_all(['header', 'footer']):
        element.decompose()
    return str(soup)

# Convert HTML content to markdown
def html_to_markdown_with_readability(html_content):
    cleaned_html = clean_html(html_content)  
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    markdown_content = markdown_converter.handle(cleaned_html)
    return markdown_content

# Save raw markdown data to the specified folder with unique filenames
def save_raw_data(raw_data: str, output_folder: str, file_name: str):
    os.makedirs(output_folder, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    file_name = f"{file_name}_{timestamp}.md"
    raw_output_path = os.path.join(output_folder, file_name)
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    print(f"Raw data saved to {raw_output_path}")
    return raw_output_path

# Functions for creating dynamic models
def create_dynamic_listing_model(field_names: List[str]) -> Type[BaseModel]:
    field_definitions = {field: (str, ...) for field in field_names}
    return create_model('DynamicListingModel', **field_definitions)

def create_listings_container_model(listing_model: Type[BaseModel]) -> Type[BaseModel]:
    return create_model('DynamicListingsContainer', listings=(List[listing_model], ...))

# Token trimming function
def trim_to_token_limit(text, model, max_tokens=120000):
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    if len(tokens) > max_tokens:
        trimmed_text = encoder.decode(tokens[:max_tokens])
        return trimmed_text
    return text

# Format data function
def format_data(data, DynamicListingsContainer, DynamicListingModel, selected_model):
    token_counts = {}
    if selected_model == "gemini-1.5-flash":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Please set the GEMINI_API_KEY environment variable")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config={
            "response_mime_type": "application/json",
            "response_schema": DynamicListingsContainer
        })
        prompt = SYSTEM_MESSAGE + "\n" + USER_MESSAGE + data
        input_tokens = model.count_tokens(prompt)
        completion = model.generate_content(prompt)
        usage_metadata = completion.usage_metadata
        token_counts = {
            "input_tokens": usage_metadata.prompt_token_count,
            "output_tokens": usage_metadata.candidates_token_count
        }
        return completion.text, token_counts
    else:
        raise ValueError(f"Unsupported model: {selected_model}")

# Save formatted data function
def save_formatted_data(formatted_data, output_folder: str, json_file_name: str, excel_file_name: str):
    os.makedirs(output_folder, exist_ok=True)
    if isinstance(formatted_data, str):
        try:
            formatted_data_dict = json.loads(formatted_data)
        except json.JSONDecodeError:
            raise ValueError("The provided formatted data is a string but not valid JSON.")
    else:
        formatted_data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data

    json_output_path = os.path.join(output_folder, json_file_name)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data_dict, f, indent=4)
    print(f"Formatted data saved to JSON at {json_output_path}")

    if isinstance(formatted_data_dict, dict):
        data_for_df = next(iter(formatted_data_dict.values())) if len(formatted_data_dict) == 1 else formatted_data_dict
    elif isinstance(formatted_data_dict, list):
        data_for_df = formatted_data_dict
    else:
        raise ValueError("Formatted data is neither a dictionary nor a list, cannot convert to DataFrame")

    try:
        df = pd.DataFrame(data_for_df)
        print("DataFrame created successfully.")
        excel_output_path = os.path.join(output_folder, excel_file_name)
        df.to_excel(excel_output_path, index=False)
        print(f"Formatted data saved to Excel at {excel_output_path}")
        return df
    except Exception as e:
        print(f"Error creating DataFrame or saving Excel: {str(e)}")
        return None

# Generate unique folder name
def generate_unique_folder_name(url):
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    url_name = re.sub(r'\W+', '_', url.split('//')[1].split('/')[0])
    return f"{url_name}_{timestamp}"

# Scrape URL function
def scrape_url(url: str, fields: List[str], selected_model: str, output_folder: str, file_number: int, markdown: str):
    try:
        save_raw_data(markdown, output_folder, f'rawData_{file_number}.md')
        DynamicListingModel = create_dynamic_listing_model(fields)
        DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
        formatted_data, token_counts = format_data(markdown, DynamicListingsContainer, DynamicListingModel, selected_model)
        save_formatted_data(formatted_data, output_folder, f'sorted_data_{file_number}.json', f'sorted_data_{file_number}.xlsx')
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return 0, 0, 0, None  