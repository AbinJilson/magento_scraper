import re
import logging
import json
from urllib.parse import urljoin, urlparse
from datetime import datetime
from scrapy import Spider, Request
from scrapy.http import HtmlResponse
from scrapy.exceptions import CloseSpider
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TimeoutError, DNSLookupError
from itemadapter import ItemAdapter
from ..items import ProductItem, CategoryItem

class MagentoSpider(Spider):
    """
    Spider for scraping products from the Magento demo store.
    Handles category navigation, product listing, and detailed product pages.
    """
    
    name = 'magento'
    allowed_domains = ['magento.softwaretestingboard.com']
    start_urls = ['https://magento.softwaretestingboard.com/']
    
    # XPath and CSS selectors
    SELECTORS = {
        # Category navigation
        'category_menu': '//nav[@class="navigation"]//ul[contains(@class, "level0")]/li',
        'category_name': './/a//span[not(contains(@class, "ui-menu-icon"))]/text()',
        'subcategory_menu': './/ul[contains(@class, "level1")]//a',
        
        # Product listing
        'product_links': '//div[contains(@class, "product-item-info")]/a',
        'product_name': './/span[contains(@class, "product-image-wrapper")]/@alt',
        'product_price': './/span[contains(@class, "price")]/text()',
        'product_image': './/span[contains(@class, "product-image-wrapper")]//img/@src',
        'next_page': '//a[contains(@class, "next")]/@href',
        
        # Product details
        'product_title': '//h1[contains(@class, "page-title")]/span/text()',
        'product_sku': [
            '//div[contains(@class, "product-info-sku")]/div[2]/text()',
            '//div[contains(@class, "product.attribute.sku")]/div[2]/text()',
            '//div[contains(@class, "product-info-sku")]//text()[contains(., "SKU#")]/parent::*',
            '//div[contains(@class, "product-info-sku")]//text()[contains(., "SKU:")]/parent::*'
        ],
        'product_description': [
            '//div[contains(@class, "product-info-description")]',
            '//div[contains(@class, "product.attribute.description")]',
            '//div[contains(@class, "product data items")]',
            '//div[contains(@class, "product-info-details")]',
            '//div[contains(@class, "product attribute overview")]'
        ],
        'product_details': '//div[contains(@class, "additional-attributes-wrapper")]//tr',
        'product_price_main': '//span[contains(@class, "price")]/span[contains(@class, "price")]/text()',
        'product_images': [
            '//div[contains(@class, "gallery-placeholder")]//img/@src',
            '//div[contains(@class, "fotorama__stage")]//img/@src'  # For full-size images
        ],
        
        # Enhanced selectors for colors and sizes
        'product_colors': [
            # New selectors based on actual page structure
            '//div[contains(@class, "swatch-attribute color")]//div[contains(@class, "swatch-option")]/@option-label',
            '//div[contains(@class, "swatch-attribute color")]//div[contains(@class, "swatch-option")]/@data-option-label',
            '//div[contains(@class, "swatch-attribute color")]//div[contains(@class, "swatch-option")]/@title',
            '//div[contains(@class, "swatch-attribute color")]//div[contains(@class, "swatch-option")]/@aria-label',
            '//div[contains(@class, "swatch-option color")]/@option-label',
            '//div[contains(@class, "swatch-option color")]/@data-option-label',
            '//div[contains(@class, "swatch-option color")]/@title',
            '//div[contains(@class, "swatch-option color")]/@aria-label',
            '//select[contains(@id, "attribute") and contains(@id, "color")]/option[position()>1]/text()',
            '//select[contains(@name, "color")]/option[position()>1]/text()',
            # Additional selectors for Magento 2.4+
            '//div[contains(@class, "swatch-attribute-options")]//div[contains(@class, "swatch-option color")]/@option-label',
            '//div[contains(@class, "swatch-opt")]//div[contains(@class, "swatch-option color")]/@option-label',
            '//div[contains(@class, "product-options-wrapper")]//div[contains(@class, "swatch-option color")]/@option-label',
            '//div[contains(@class, "swatch-attribute-options")]//div[contains(@class, "swatch-option color")]/@aria-label',
            '//div[contains(@class, "swatch-opt")]//div[contains(@class, "swatch-option color")]/@aria-label',
            '//div[contains(@class, "product-options-wrapper")]//div[contains(@class, "swatch-option color")]/@aria-label',
            '//div[@attribute-code="color"]//div[contains(@class, "swatch-option")]/@option-label',
            '//div[contains(@class, "swatch-attribute-selected-option") and contains(text(), "Color")]/following-sibling::div[1]/text()',
        ],
        'product_sizes': [
            # New selectors based on actual page structure
            '//div[contains(@class, "swatch-attribute size")]//div[contains(@class, "swatch-option")]/@option-label',
            '//div[contains(@class, "swatch-attribute size")]//div[contains(@class, "swatch-option")]/@data-option-label',
            '//div[contains(@class, "swatch-attribute size")]//div[contains(@class, "swatch-option")]/@title',
            '//div[contains(@class, "swatch-attribute size")]//div[contains(@class, "swatch-option")]/@aria-label',
            '//div[contains(@class, "swatch-option text")]/@option-label',
            '//div[contains(@class, "swatch-option text")]/@data-option-label',
            '//div[contains(@class, "swatch-option text")]/@title',
            '//div[contains(@class, "swatch-option text")]/@aria-label',
            '//select[contains(@id, "attribute") and contains(@id, "size")]/option[position()>1]/text()',
            '//select[contains(@name, "size")]/option[position()>1]/text()',
            '//select[contains(@id, "attribute") and contains(@id, "size")]/option[position()>1]/@title',
            # Additional selectors for Magento 2.4+
            '//div[contains(@class, "swatch-attribute-options")]//div[contains(@class, "swatch-option text")]/@option-label',
            '//div[contains(@class, "swatch-opt")]//div[contains(@class, "swatch-option text")]/@option-label',
            '//div[contains(@class, "product-options-wrapper")]//div[contains(@class, "swatch-option text")]/@option-label',
            '//div[contains(@class, "swatch-attribute-options")]//div[contains(@class, "swatch-option text")]/@aria-label',
            '//div[contains(@class, "swatch-opt")]//div[contains(@class, "swatch-option text")]/@aria-label',
            '//div[contains(@class, "product-options-wrapper")]//div[contains(@class, "swatch-option text")]/@aria-label',
            '//div[@attribute-code="size"]//div[contains(@class, "swatch-option")]/@option-label',
            '//div[contains(@class, "swatch-attribute-selected-option") and contains(text(), "Size")]/following-sibling::div[1]/text()',
            '//div[contains(@class, "swatch-attribute-label") and contains(., "Size")]/following-sibling::div[contains(@class, "swatch-attribute-options")]//div[contains(@class, "swatch-option")]/@option-label',
        ],
        'product_availability': '//div[contains(@class, "stock")]/span[contains(@class, "available")]/text()',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.processed_urls = set()
        
    def _extract_parent_category(self, url):
        """Extract parent category from URL using a more robust method."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.lower().split('/') if p]

        # If the path has fewer than 2 parts, it's a main category page (e.g., /women.html)
        if len(path_parts) < 2:
            return ''

        # The parent category is the directory part of the path (e.g., 'women' in '/women/tops-women.html')
        parent_part = path_parts[-2]

        category_map = {
            'women': 'Women',
            'men': 'Men',
            'gear': 'Gear',
            'training': 'Training',
        }

        return category_map.get(parent_part, '')

    def parse(self, response, **kwargs):
        """
        Parse the main page and extract category links with proper hierarchy.
        """
        self.logger.info(f"Parsing main page: {response.url}")
        
        # Extract main category links
        for category in response.xpath(self.SELECTORS['category_menu']):
            category_name = category.xpath(self.SELECTORS['category_name']).get()
            if not category_name:
                continue
                
            category_name = category_name.strip()
            
            # Skip unwanted categories
            if category_name.lower() in ['home', 'sale']:
                continue
            
            # Get the main category URL
            category_url = category.xpath('.//a[1]/@href').get()
            if not category_url:
                continue
                
            category_url = category_url.strip()
            
            # Determine if this is a main category by its name
            is_main_category = category_name.lower() in ['women', 'men', 'gear', 'training']
            
            if is_main_category:
                # This is a main category (like Women, Men, Gear)
                main_category_item = CategoryItem(
                    name=category_name,
                    url=category_url,
                    parent_category='',
                    level=0,
                    timestamp=datetime.utcnow().isoformat()
                )
                yield main_category_item
                
                # Process subcategories if they exist
                subcategories = category.xpath(self.SELECTORS['subcategory_menu'])
                for subcat in subcategories:
                    subcat_name = subcat.xpath('text()').get('').strip()
                    subcat_url = subcat.xpath('@href').get('').strip()
                    
                    if not all([subcat_name, subcat_url]):
                        continue
                    
                    # Create subcategory item
                    subcategory_item = CategoryItem(
                        name=subcat_name,
                        url=subcat_url,
                        parent_category=category_name,
                        level=1,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    yield subcategory_item
                    
                    # Follow subcategory to parse products
                    yield response.follow(
                        subcat_url,
                        callback=self.parse_category,
                        meta={
                            'category': subcat_name,  # Current category is the subcategory
                            'subcategory': '',
                            'parent_category': category_name,  # Parent is the main category
                            'breadcrumbs': [category_name, subcat_name]  # Full path
                        },
                        dont_filter=True
                    )
                
                # Also parse the main category page for products
                yield response.follow(
                    category_url,
                    callback=self.parse_category,
                    meta={
                        'category': category_name,
                        'parent_category': '',  # Top-level category has no parent
                        'breadcrumbs': [category_name]
                    }
                )
            else:
                # This is a standalone category (like Tops, Bottoms under Women)
                parent_category = self._extract_parent_category(category_url)
                
                # Create category item
                category_item = CategoryItem(
                    name=category_name,
                    url=category_url,
                    parent_category=parent_category,
                    level=1 if parent_category else 0,
                    timestamp=datetime.utcnow().isoformat()
                )
                yield category_item
                
                # Follow to parse products
                yield response.follow(
                    category_url,
                    callback=self.parse_category,
                    meta={
                        'category': category_name,
                        'subcategory': '',
                        'parent_category': parent_category if parent_category else '',
                        'breadcrumbs': [parent_category, category_name] if parent_category else [category_name]
                    }
                )
    
    def check_nested_categories(self, response):
        """Check for and process nested subcategories (level 2)."""
        # Check if there are nested subcategories
        nested_categories = response.xpath('//div[contains(@class, "categories")]//a')
        
        if nested_categories:
            parent_category = response.meta.get('parent_category', '')
            subcategory = response.meta.get('subcategory', '')
            breadcrumbs = response.meta.get('breadcrumbs', [])
            level = response.meta.get('level', 1) + 1
            
            for nested_cat in nested_categories:
                nested_name = nested_cat.xpath('text()').get('').strip()
                nested_url = nested_cat.xpath('@href').get('').strip()
                
                if not all([nested_name, nested_url]):
                    continue
                
                # Create nested category item
                nested_item = CategoryItem(
                    name=nested_name,
                    url=nested_url,
                    parent_category=subcategory,
                    level=level,
                    timestamp=datetime.utcnow().isoformat()
                )
                yield nested_item
                
                # Update breadcrumbs for the nested level
                nested_breadcrumbs = breadcrumbs + [nested_name]
                
                # Follow nested category to parse products
                yield response.follow(
                    nested_url,
                    callback=self.parse_category,
                    meta={
                        'category': parent_category,
                        'subcategory': subcategory,
                        'nested_category': nested_name,
                        'breadcrumbs': nested_breadcrumbs
                    }
                )
    
    def parse_category(self, response):
        """
        Parse a category page and extract product links.
        """
        self.logger.info(f"Parsing category: {response.url}")

        parent_category = response.meta.get('parent_category', '')
        category = response.meta.get('category', '')

        # Extract product links
        product_links = response.xpath(self.SELECTORS['product_links'])
        if not product_links:
            self.logger.warning(f"No products found on category page: {response.url}")
            return

        for product_info in product_links:
            product_url = product_info.xpath('@href').get()
            if not product_url:
                continue
            
            product_url = response.urljoin(product_url)

            # Follow product link
            yield Request(
                product_url,
                callback=self.parse_product,
                cb_kwargs={
                    'parent_category': parent_category,
                    'category': category
                }
            )

        # Handle pagination
        next_page = response.xpath(self.SELECTORS['next_page']).get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                meta=response.meta,
                dont_filter=True  # Allow multiple requests to same URL with different meta
            )

    def parse_product(self, response, parent_category=None, category=None):
        """
        Parse a product page and extract detailed information using embedded JSON data.
        """
        self.logger.info(f"Parsing product: {response.url}")
        product_item = ProductItem()
        product_item['parent_category'] = parent_category
        product_item['category'] = category
        product_item['url'] = response.url

        # Basic details from primary selectors
        product_item['name'] = response.css('span[data-ui-id="page-title-wrapper"]::text').get('').strip()
        product_item['sku'] = response.css('div[itemprop="sku"]::text').get('').strip()
        description_parts = response.css('div.product.attribute.description .value ::text').getall()
        product_item['description'] = ' '.join(part.strip() for part in description_parts if part.strip())

        images = set()
        colors = set()
        sizes = set()

        # --- Combined JSON Extraction Logic ---
        # Find all x-magento-init scripts and try to parse them
        scripts = response.xpath('//script[@type="text/x-magento-init"]/text()').getall()
        for script_text in scripts:
            try:
                data = json.loads(script_text)
                
                # 1. Try to get swatch data (colors, sizes, and some images)
                swatch_key = '[data-role=swatch-options]'
                if swatch_key in data and 'Magento_Swatches/js/swatch-renderer' in data.get(swatch_key, {}):
                    renderer_data = data[swatch_key]['Magento_Swatches/js/swatch-renderer']
                    config = renderer_data.get('jsonConfig', {})

                    if 'images' in config:
                        for product_images in config['images'].values():
                            for image in product_images:
                                if image.get('full'):
                                    images.add(image['full'])

                    if 'attributes' in config:
                        for attr in config['attributes'].values():
                            if attr.get('code') == 'color':
                                for option in attr.get('options', []):
                                    if option.get('label'):
                                        colors.add(option['label'])
                            elif attr.get('code') == 'size':
                                for option in attr.get('options', []):
                                    if option.get('label'):
                                        sizes.add(option['label'])

                # 2. Try to get gallery data (main product images)
                gallery_key = '[data-gallery-role=gallery-placeholder]'
                if gallery_key in data and 'mage/gallery/gallery' in data.get(gallery_key, {}):
                    gallery_config = data[gallery_key].get('mage/gallery/gallery', {})
                    for image in gallery_config.get('data', []):
                        if image.get('full'):
                            images.add(image['full'])

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.debug(f"Could not parse JSON from a script tag on {response.url}: {e}")

        # --- Fallback to XPath if JSON fails ---
        if not colors:
            color_labels = response.xpath('|'.join(self.SELECTORS['product_colors'])).getall()
            colors.update(label.strip() for label in color_labels if label.strip())

        if not sizes:
            size_labels = response.xpath('|'.join(self.SELECTORS['product_sizes'])).getall()
            sizes.update(label.strip() for label in size_labels if label.strip())

        # Assign extracted data to the item
        product_item['images'] = sorted(list(images))
        product_item['colors'] = sorted(list(colors))
        product_item['sizes'] = sorted(list(sizes))
        
        product_item.setdefault('timestamp', datetime.now().isoformat())
        product_item.setdefault('spider', self.name)

        self.logger.debug(f"Scraped item: {product_item}")
        yield product_item
