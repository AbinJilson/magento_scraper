import logging
import hashlib
from pathlib import Path
from datetime import datetime
from itemadapter import ItemAdapter, is_item
from scrapy.exceptions import DropItem
from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request
from PIL import Image
import json

logger = logging.getLogger(__name__)

class MagentoScraperPipeline:
    """
    Main pipeline for processing scraped items with comprehensive validation,
    cleaning, and data enrichment.
    """
    
    def __init__(self, stats):
        self.stats = stats
        self.seen_urls = set()
        self.exporters = {}
        self.files = {}
        
    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from crawler."""
        return cls(stats=crawler.stats)
    
    def open_spider(self, spider):
        """Initialize resources when spider is opened."""
        self.stats.set_value('items_processed', 0)
        self.stats.set_value('items_dropped', 0)
        
        # Create output directory if it doesn't exist
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Initialize JSON exporter
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = output_dir / f'{spider.name}_{timestamp}.jsonl'
        self.files[spider] = open(file_path, 'wb')
        self.exporters[spider] = JsonItemExporter(
            self.files[spider],
            encoding='utf-8',
            indent=2,
            ensure_ascii=False
        )
        self.exporters[spider].start_exporting()
    
    def close_spider(self, spider):
        """Clean up resources when spider is closed."""
        if spider in self.exporters:
            self.exporters[spider].finish_exporting()
            self.files[spider].close()
            
            # Log pipeline stats
            logger.info(f"Items processed: {self.stats.get_value('items_processed', 0)}")
            logger.info(f"Items dropped: {self.stats.get_value('items_dropped', 0)}")
    
    def process_item(self, item, spider):
        """Process each item through the pipeline."""
        if not is_item(item):
            return item
            
        adapter = ItemAdapter(item)
        
        try:
            # Check for duplicate items using URL
            item_url = adapter.get('url')
            if not item_url:
                raise DropItem("Missing URL in item")
                
            # Create a unique identifier for the item
            item_id = self._get_item_id(adapter)
            
            if item_id in self.seen_urls:
                self.stats.inc_value('items_dropped')
                raise DropItem(f"Duplicate item found: {item_url}")
            
            self.seen_urls.add(item_id)
            
            # Basic validation
            if not adapter.get('name'):
                raise DropItem(f"Missing name in item: {item_url}")
            
            # Clean and validate data
            self._clean_data(adapter)
            
            # Add metadata
            self._add_metadata(adapter, spider)
            
            # Export the item
            if spider in self.exporters:
                self.exporters[spider].export_item(item)
            
            # Update stats
            self.stats.inc_value('items_processed')
            
            return item
            
        except DropItem as e:
            self.stats.inc_value('items_dropped')
            logger.warning(f"Dropped item: {e}")
            raise
            
        except Exception as e:
            self.stats.inc_value('items_dropped')
            logger.error(f"Error processing item: {e}", exc_info=True)
            raise DropItem(f"Error processing item: {e}")
    
    def _get_item_id(self, adapter):
        """Generate a unique ID for the item based on its URL and SKU."""
        url = adapter.get('url', '')
        sku = adapter.get('sku', '')
        return hashlib.md5(f"{url}:{sku}".encode('utf-8')).hexdigest()
    
    def _clean_data(self, adapter):
        """Clean and validate item data."""
        # Clean text fields
        text_fields = ['name', 'description', 'short_description']
        for field in text_fields:
            if field in adapter:
                if isinstance(adapter[field], list):
                    adapter[field] = [
                        str(text).strip() 
                        for text in adapter[field] 
                        if text is not None
                    ]
                elif adapter[field] is not None:
                    adapter[field] = str(adapter[field]).strip()
        
        # Ensure list fields are lists
        list_fields = ['colors', 'sizes', 'image_urls', 'variants']
        for field in list_fields:
            if field in adapter and not isinstance(adapter.get(field), list):
                adapter[field] = [adapter[field]] if adapter.get(field) is not None else []
        
        # Clean and validate URLs
        if 'image_urls' in adapter:
            adapter['image_urls'] = [
                url for url in adapter['image_urls'] 
                if url and isinstance(url, str) and url.startswith(('http://', 'https://'))
            ]
    
    def _add_metadata(self, adapter, spider):
        """Add metadata to the item."""
        # Add timestamp if not present
        if 'timestamp' not in adapter:
            adapter['timestamp'] = datetime.utcnow().isoformat()
        
        # Add spider name only if the item has a spider field
        if hasattr(adapter.item, 'fields') and 'spider' in adapter.item.fields and 'spider' not in adapter:
            adapter['spider'] = spider.name


class CustomImagesPipeline(ImagesPipeline):
    """
    Custom image pipeline that extends the default ImagesPipeline
    to handle image downloading and processing.
    """
    
    def get_media_requests(self, item, info):
        """Generate a media request object for each image URL."""
        if 'image_urls' not in item:
            return []
            
        return [
            Request(
                url=url,
                meta={
                    'item': item,
                    'image_url': url,
                    'filename': self._get_image_filename(item, url)
                }
            )
            for url in item.get('image_urls', [])
            if url and isinstance(url, str)
        ]
    
    def file_path(self, request, response=None, info=None, *, item=None):
        """Return the filename for the downloaded image."""
        return request.meta.get('filename', '')
    
    def item_completed(self, results, item, info):
        """Called when all image downloads for an item are completed."""
        if 'images' not in item:
            item['images'] = []
            
        # Add image paths to the item
        for ok, image_info in results:
            if ok:
                item['images'].append({
                    'url': image_info.get('url', ''),
                    'path': image_info.get('path', ''),
                    'checksum': image_info.get('checksum', ''),
                    'status': 'downloaded'
                })
            else:
                item['images'].append({
                    'url': image_info.get('url', ''),
                    'status': 'failed',
                    'error': str(image_info.get('exception', 'Unknown error'))
                })
                
        return item
    
    def _get_image_filename(self, item, url):
        """Generate a filename for the downloaded image."""
        # Use item SKU and URL hash to create a unique filename
        sku = item.get('sku', 'unknown')
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        extension = url.split('.')[-1].lower()
        
        # Ensure the extension is valid
        if len(extension) > 5 or '/' in extension or '?' in extension:
            extension = 'jpg'
            
        return f"{sku}_{url_hash[:8]}.{extension}"
