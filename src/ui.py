import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime
import re
from urllib.parse import urlparse
import os
from src.scraper import (
    fetch_html_selenium,
    save_raw_data,
    format_data,
    save_formatted_data,
    html_to_markdown_with_readability,
    create_dynamic_listing_model,
    create_listings_container_model,
    scrape_url,
    init_driver,
    generate_unique_folder_name
)

def main():
    # Initialize Streamlit app
    st.set_page_config(page_title="Universal Web Scraper", page_icon="🦑")
    st.title("Universal Web Scraper 🦑")

    # Initialize session state variables
    if 'scraping_state' not in st.session_state:
        st.session_state['scraping_state'] = 'idle'  # Possible states: 'idle', 'waiting', 'scraping', 'completed'
    if 'results' not in st.session_state:
        st.session_state['results'] = None
    if 'driver' not in st.session_state:
        st.session_state['driver'] = None

    # Sidebar components
    st.sidebar.title("Web Scraper Settings")

    # Model selection
    model_selection = st.sidebar.selectbox("Select Model", options=["gemini-1.5-flash","gpt-4o-mini"])

    # URL input
    url_input = st.sidebar.text_input("Enter URL(s) separated by whitespace")
    urls = url_input.strip().split()  # Process URLs
    num_urls = len(urls)

    # Fields to extract
    fields = st_tags_sidebar(
        label='Enter Fields to Extract:',
        text='Press enter to add a field',
        value=[],
        suggestions=[],
        maxtags=-1,
        key='fields_input'
    )

    st.sidebar.markdown("---")

    # Main action button
    if st.sidebar.button("SCRAPE DATA", type="primary"):
        if url_input.strip() == "":
            st.error("Please enter at least one URL.")
        elif len(fields) == 0:
            st.error("Please enter at least one field to extract.")
        else:
            # Set up scraping parameters in session state
            st.session_state['urls'] = url_input.strip().split()
            st.session_state['fields'] = fields
            st.session_state['model_selection'] = model_selection
            st.session_state['scraping_state'] = 'scraping'

    # Scraping logic
    if st.session_state['scraping_state'] == 'scraping':
        with st.spinner('Scraping in progress...'):
            output_folder = os.path.join('output', generate_unique_folder_name(st.session_state['urls'][0]))
            os.makedirs(output_folder, exist_ok=True)

            all_data = []

            for i, url in enumerate(st.session_state['urls'], start=1):
                # Fetch HTML
                raw_html = fetch_html_selenium(url, attended_mode=False)
                markdown = html_to_markdown_with_readability(raw_html)
                save_raw_data(markdown, output_folder, f'rawData_{i}.md')

                # Create dynamic models and format data
                DynamicListingModel = create_dynamic_listing_model(st.session_state['fields'])
                DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
                formatted_data, token_counts = format_data(
                    markdown, DynamicListingsContainer, DynamicListingModel, st.session_state['model_selection']
                )
                df = save_formatted_data(formatted_data, output_folder, f'sorted_data_{i}.json', f'sorted_data_{i}.xlsx')
                all_data.append(formatted_data)

            # Save results
            st.session_state['results'] = {
                'data': all_data,
                'output_folder': output_folder,
            }
            st.session_state['scraping_state'] = 'completed'

    # Display results
    if st.session_state['scraping_state'] == 'completed' and st.session_state['results']:
        results = st.session_state['results']
        all_data = results['data']
        output_folder = results['output_folder']

        st.subheader("Scraping Results")
        for i, data in enumerate(all_data, start=1):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    st.error(f"Failed to parse data as JSON for URL {i}")
                    continue

            if isinstance(data, dict):
                if 'listings' in data and isinstance(data['listings'], list):
                    df = pd.DataFrame(data['listings'])
                else:
                    df = pd.DataFrame([data])
            elif hasattr(data, 'listings') and isinstance(data.listings, list):
                listings = [item.dict() for item in data.listings]
                df = pd.DataFrame(listings)
            else:
                st.error(f"Unexpected data format for URL {i}")
                continue
            st.dataframe(df, use_container_width=True)

        # Download options
        st.subheader("Download Extracted Data")
        col1, col2 = st.columns(2)
        with col1:
            json_data = json.dumps(all_data, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o), indent=4)
            st.download_button("Download JSON", data=json_data, file_name="scraped_data.json")
        with col2:
            all_listings = []
            for data in all_data:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                if isinstance(data, dict) and 'listings' in data:
                    all_listings.extend(data['listings'])
                elif hasattr(data, 'listings'):
                    all_listings.extend([item.dict() for item in data.listings])
                else:
                    all_listings.append(data)

            combined_df = pd.DataFrame(all_listings)
            st.download_button("Download CSV", data=combined_df.to_csv(index=False), file_name="scraped_data.csv")

        st.success(f"Scraping completed. Results saved in {output_folder}")

    # Reset scraping state
    if st.sidebar.button("Clear Results"):
        st.session_state['scraping_state'] = 'idle'
        st.session_state['results'] = None

if __name__ =="__main__":
    main()