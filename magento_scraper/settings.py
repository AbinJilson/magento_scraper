# Scrapy settings for magento_scraper project
import os
from pathlib import Path

# Project information
BOT_NAME = 'magento_scraper'
SPIDER_MODULES = ['magento_scraper.spiders']
NEWSPIDER_MODULE = 'magento_scraper.spiders'

# Core settings
ROBOTSTXT_OBEY = True  # Respect robots.txt rules
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Performance settings
CONCURRENT_REQUESTS = 2  # Reduced to be gentle on the target site
DOWNLOAD_DELAY = 2.0  # 2 second delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True  # Add randomness to the delay
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_ITEMS = 100

# Caching and retry
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408, 429, 522, 524]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Retry middleware
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408, 429]

# Security settings
COOKIES_ENABLED = False
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Item pipelines
ITEM_PIPELINES = {
    'magento_scraper.pipelines.MagentoScraperPipeline': 300,
    'scrapy.pipelines.images.ImagesPipeline': 1,
}

# Images pipeline settings
IMAGES_STORE = os.path.join(Path.home(), 'scrapy_images')
IMAGES_URLS_FIELD = 'images'
IMAGES_RESULT_FIELD = 'images'
IMAGES_THUMBS = {
    'small': (50, 50),
    'big': (270, 270),
}

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.selectreactor.SelectReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Configure maximum depth for requests
DEPTH_LIMIT = 10
DEPTH_PRIORITY = 1

# Configure item exporters
FEED_EXPORTERS = {
    'json': 'scrapy.exporters.JsonItemExporter',
    'jsonlines': 'scrapy.exporters.JsonLinesItemExporter',
}

# Configure file download timeout
DOWNLOAD_TIMEOUT = 180  # 3 minutes

# Disable redirects (enabled by default)
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5
