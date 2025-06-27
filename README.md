# Magento E-commerce Scraper

A Scrapy-based web scraper for extracting product and category data from Magento-based e-commerce websites.

## Features

- Extracts product details (name, price, description, SKU, etc.)
- Handles categories and subcategories
- Manages pagination
- Respects robots.txt and implements delays
- Saves images using Scrapy's Images Pipeline
- Handles duplicate items
- Clean and structured data output

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd magento_scraper
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Modify the settings in `magento_scraper/settings.py` as needed:
- Adjust `DOWNLOAD_DELAY` to be respectful to the target website
- Configure `CONCURRENT_REQUESTS` based on your needs
- Set up `IMAGES_STORE` to specify where to save downloaded images

## Available Spiders

1. **womens**: Scrapes Women's category products
   ```bash
   scrapy crawl womens -o output/womens_products.json
   ```

## Output

By default, the spider outputs data in JSON format. You can change the output format by modifying the file extension in the output path (e.g., `.csv`, `.jl`, `.jsonlines`).

## Rate Limiting

The spider is configured with conservative defaults to be respectful to the target website. You can adjust these settings in `settings.py`:

```python
# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 2.0
RANDOMIZE_DOWNLOAD_DELAY = True
```

## Data Models

### CategoryItem
- `name`: Category name
- `url`: Category URL
- `parent_category`: Parent category name
- `level`: Category level in the hierarchy
- `timestamp`: When the item was scraped

### ProductItem
- `name`: Product name
- `sku`: Product SKU
- `url`: Product URL
- `category`: Product category
- `price`: Current price
- `regular_price`: Regular price (if on sale)
- `description`: Product description
- `image_urls`: List of image URLs
- `in_stock`: Boolean indicating if the product is in stock
- `colors`: Available colors
- `sizes`: Available sizes
- `timestamp`: When the item was scraped

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
