# Magento E-commerce Scraper

A Scrapy-based web scraper for extracting product and category data from Magento-based e-commerce websites.

## Features

- Extracts comprehensive product details including:
  - Product name and SKU
  - Price information
  - Product descriptions
  - Product images
  - Categories and subcategories
- Handles pagination for product listings
- Respects website's robots.txt and implements request delays
- Saves images using Scrapy's Images Pipeline
- Handles duplicate items and request errors gracefully
- Outputs clean, structured JSON data

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AbinJilson/magento_scraper.git
   cd magento_scraper
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   # source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Modify the following settings in `magento_scraper/settings.py` if needed:
- `DOWNLOAD_DELAY`: Time (in seconds) to wait between requests (default: 1.5s)
- `CONCURRENT_REQUESTS`: Number of concurrent requests (default: 2)
- `IMAGES_STORE`: Directory to save downloaded images (default: 'images')
- `FEED_FORMAT`: Output format (default: 'json')
- `FEED_URI`: Output file path (default: 'output/products.json')

## Usage

### Running the Spider

To start scraping, run:

```bash
scrapy crawl magento -o output/products.json
```

### Output

The scraper will create:
1. A JSON file with all product data (default: `output/products.json`)
2. An `images/` directory containing downloaded product images

## Project Structure

```
magento_scraper/
├── magento_scraper/
│   ├── spiders/
│   │   └── magento_spider.py  # Main spider implementation
│   ├── items.py               # Data structure definitions
│   ├── middlewares.py         # Custom middlewares
│   ├── pipelines.py           # Item processing pipelines
│   └── settings.py            # Project settings
├── output/                    # Default output directory
├── images/                    # Downloaded images (created after first run)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Error Handling

The spider includes comprehensive error handling for:
- HTTP errors (404, 500, etc.)
- Timeout errors
- DNS lookup failures
- Invalid responses
- Missing data fields

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is for educational purposes only. Please respect the target website's terms of service and robots.txt rules. Always obtain proper authorization before scraping any website.
