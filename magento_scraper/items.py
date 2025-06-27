import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Identity, Compose
from w3lib.html import remove_tags, strip_html5_whitespace, replace_escape_chars
from datetime import datetime
import re

class DefaultEmptyString:
    """Return default value if input is None or empty."""
    def __init__(self, default=''):
        self.default = default
    
    def __call__(self, values):
        return values[0] if values and values[0] else self.default

def clean_text(text):
    """Clean and normalize text data."""
    if not text:
        return ''
    # Convert to string in case it's not
    text = str(text)
    # Remove HTML tags and normalize whitespace
    text = re.sub(r'\s+', ' ', strip_html5_whitespace(text)).strip()
    return text

def extract_price(value):
    """Extract numeric value from price string."""
    if not value:
        return None
    # Remove all non-numeric characters except decimal point
    try:
        return float(re.sub(r'[^\d.]', '', str(value)))
    except (ValueError, TypeError):
        return None

class CategoryItem(scrapy.Item):
    """Container for category data."""
    # Required fields
    name = scrapy.Field(
        input_processor=MapCompose(
            remove_tags,
            clean_text,
            str.title  # Ensure consistent capitalization
        ),
        output_processor=TakeFirst()
    )
    url = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    parent_category = scrapy.Field(
        input_processor=MapCompose(
            remove_tags,
            clean_text,
            str.lower
        ),
        output_processor=TakeFirst(),
        default=''
    )
    level = scrapy.Field(
        output_processor=TakeFirst(),
        default=0
    )
    breadcrumbs = scrapy.Field(
        input_processor=Identity(),
        default=[]
    )
    # Timestamp when the item was scraped (ISO 8601 format)
    timestamp = scrapy.Field(
        output_processor=TakeFirst(),
        default=lambda: datetime.utcnow().isoformat()
    )
    
    def __repr__(self):
        return f"<CategoryItem {self.get('name')}>"

class ProductItem(scrapy.Item):
    """Container for product data with comprehensive field definitions."""
    # Basic product information
    name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
        required=True
    )
    sku = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst(),
        required=True
    )
    url = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst(),
        required=True
    )
    
    # Category information
    category = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    parent_category = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    nested_category = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    # Pricing information
    price = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text, extract_price),
        output_processor=TakeFirst()
    )
    regular_price = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text, extract_price),
        output_processor=TakeFirst()
    )
    special_price = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text, extract_price),
        output_processor=TakeFirst()
    )
    currency = scrapy.Field(
        output_processor=TakeFirst(),
        default='USD'
    )
    
    # Product details
    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text, replace_escape_chars),
        output_processor=DefaultEmptyString()
    )
    short_description = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text, replace_escape_chars),
        output_processor=TakeFirst()
    )
    
    # Media
    image_urls = scrapy.Field(
        default=[],
        serializer=lambda x: [str(url) for url in x] if x else []
    )
    images = scrapy.Field()
    
    # Availability
    in_stock = scrapy.Field(
        output_processor=TakeFirst(),
        default=True
    )
    stock_quantity = scrapy.Field(
        output_processor=TakeFirst(),
        default=0
    )
    availability = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    # Product variants
    colors = scrapy.Field(
        default=[]
    )
    sizes = scrapy.Field(
        default=[]
    )
    variants = scrapy.Field(
        default=[]
    )
    
    # Metadata
    timestamp = scrapy.Field(
        output_processor=TakeFirst(),
        default=lambda: datetime.utcnow().isoformat()
    )
    spider = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    # SEO
    meta_title = scrapy.Field(
        output_processor=TakeFirst()
    )
    meta_description = scrapy.Field(
        output_processor=TakeFirst()
    )
    meta_keywords = scrapy.Field(
        output_processor=TakeFirst()
    )
    
    # Product attributes
    attributes = scrapy.Field(
        default={}
    )
    
    # Review information
    rating = scrapy.Field(
        output_processor=TakeFirst()
    )
    review_count = scrapy.Field(
        output_processor=TakeFirst(),
        default=0
    )
    
    # Product identification
    brand = scrapy.Field(
        output_processor=TakeFirst()
    )
    mpn = scrapy.Field(
        output_processor=TakeFirst()
    )  # Manufacturer Part Number
    gtin = scrapy.Field(
        output_processor=TakeFirst()
    )  # Global Trade Item Number
    
    # Product status
    is_new = scrapy.Field(
        output_processor=TakeFirst(),
        default=False
    )
    is_bestseller = scrapy.Field(
        output_processor=TakeFirst(),
        default=False
    )
    
    # Additional metadata
    extra = scrapy.Field(
        default={}
    )
    parse_error = scrapy.Field(
        output_processor=TakeFirst(),
        default=None
    )
    
    def __repr__(self):
        return f"<ProductItem {self.get('name')} ({self.get('sku')})>"
