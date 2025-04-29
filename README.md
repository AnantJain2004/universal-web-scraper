# Universal Web Scraper 🦑

A flexible and powerful web scraping tool that combines browser automation with AI-powered data extraction. This project uses Selenium for browser automation and large language models (LLMs) to intelligently extract structured data from websites.

## Features

- **AI-Powered Extraction**: Uses LLMs to intelligently identify and extract data from web pages
- **Dynamic Field Selection**: Specify exactly which fields you want to extract
- **Multi-URL Support**: Process multiple URLs in a single run
- **Multiple Export Formats**: Export data as JSON, CSV, or Excel
- **Clean Streamlit UI**: User-friendly interface for easy operation
- **Flexible Model Selection**: Choose between different AI models for extraction

## Project Structure

```
universal-web-scraper/
├── src/                # Source code
│   ├── __init__.py
│   ├── ui.py           # Streamlit user interface
│   ├── scraper.py      # Core scraping functionality
│   ├── assets.py       # Configuration and constants
├── output/             # Output directory for scraped data
├── tests/              # Test directory (for future testing)
│   └── __init__.py
├── app.py              # Application entry point
├── requirements.txt    # Dependencies
├── README.md           # This file
└── .gitignore          # Git ignore configuration
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/universal-web-scraper.git
cd universal-web-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your API key as an environment variable:
```bash
# Linux/macOS
export GEMINI_API_KEY="your_api_key_here"

# Windows
set GEMINI_API_KEY=your_api_key_here
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Enter the URL(s) you want to scrape in the sidebar
3. Enter the fields you want to extract (e.g., "title", "price", "description")
4. Select the AI model to use for extraction
5. Click "SCRAPE DATA" to start the process
6. View the extracted data in tabular format
7. Download the data as JSON or CSV

## How It Works

1. **Browser Automation**: The app uses Selenium with Edge WebDriver to load web pages and simulate scrolling
2. **HTML Processing**: The HTML is cleaned and converted to markdown for better text extraction
3. **AI Extraction**: The markdown is sent to an LLM with instructions to extract specific fields
4. **Data Formatting**: Structured data is returned as JSON and converted to various formats
5. **Results Display**: Data is shown in the UI and saved to the output directory

## Requirements

- Python 3.8+
- Microsoft Edge (for WebDriver)
- Internet connection
- API key for the selected AI model

## Future Improvements

- [ ] Add support for additional browsers
- [ ] Implement proxy rotation for anonymity
- [ ] Add authentication support for protected pages
- [ ] Create a scheduling system for periodic scraping
- [ ] Expand the AI model options

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is intended for educational purposes and legitimate data collection only. Always respect robots.txt files and website terms of service. Be responsible and ethical when scraping websites.