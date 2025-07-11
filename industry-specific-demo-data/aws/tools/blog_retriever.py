#
# Copyright 2025 Amazon.com, Inc. and its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#   http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
#

import requests
from bs4 import BeautifulSoup
import logging
import argparse
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
import re

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Default error response
systemError = {
    "status": "error",
    "message": "We are currently unable to retrieve the blog post. Please try again later."
}

def extract_metadata(soup, url):
    """
    Extract metadata from the blog post HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        url (str): Original URL of the blog post
        
    Returns:
        dict: Extracted metadata
    """
    metadata = {
        "url": url,
        "title": "",
        "author": "",
        "published_date": "",
        "description": "",
        "tags": [],
        "canonical_url": url
    }
    
    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        metadata["title"] = title_tag.get_text().strip()
    
    # Try to get better title from h1 or article title
    h1_tag = soup.find('h1')
    if h1_tag and len(h1_tag.get_text().strip()) > len(metadata["title"]):
        metadata["title"] = h1_tag.get_text().strip()
    
    # Extract meta tags
    meta_tags = soup.find_all('meta')
    for tag in meta_tags:
        # Description
        if tag.get('name') == 'description' or tag.get('property') == 'og:description':
            metadata["description"] = tag.get('content', '')
        
        # Author
        elif tag.get('name') == 'author' or tag.get('property') == 'article:author':
            metadata["author"] = tag.get('content', '')
        
        # Published date
        elif tag.get('property') == 'article:published_time' or tag.get('name') == 'date':
            metadata["published_date"] = tag.get('content', '')
        
        # Canonical URL
        elif tag.get('property') == 'og:url':
            metadata["canonical_url"] = tag.get('content', url)
    
    # Try to extract author from common selectors
    if not metadata["author"]:
        author_selectors = [
            '.author', '.byline', '[rel="author"]', '.post-author',
            '.article-author', '.entry-author'
        ]
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                metadata["author"] = author_elem.get_text().strip()
                break
    
    # Try to extract published date from common selectors
    if not metadata["published_date"]:
        date_selectors = [
            '.published', '.date', '.post-date', '.entry-date',
            'time[datetime]', '.article-date'
        ]
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if date_elem.get('datetime'):
                    metadata["published_date"] = date_elem.get('datetime')
                else:
                    metadata["published_date"] = date_elem.get_text().strip()
                break
    
    # Extract tags/categories
    tag_selectors = [
        '.tags a', '.categories a', '.post-tags a',
        '.entry-tags a', '.article-tags a'
    ]
    for selector in tag_selectors:
        tag_elements = soup.select(selector)
        if tag_elements:
            metadata["tags"] = [tag.get_text().strip() for tag in tag_elements]
            break
    
    return metadata

def extract_content(soup):
    """
    Extract the main content from the blog post HTML.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        str: Extracted main content
    """
    # Common content selectors (ordered by priority)
    content_selectors = [
        'article',
        '.post-content',
        '.entry-content', 
        '.article-content',
        '.content',
        '.post-body',
        '.entry-body',
        '.article-body',
        'main',
        '.main-content',
        'articleBody',
        'wn-body'
    ]
    
    content = ""
    
    # Try each selector until we find content
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            # Remove unwanted elements
            for unwanted in content_elem.select('script, style, nav, aside, .sidebar, .comments, .social-share'):
                unwanted.decompose()
            
            content = content_elem.get_text(separator='\n', strip=True)
            if len(content) > 200:  # Only use if substantial content
                break
    
    # Fallback: get all paragraph text if no main content found
    if not content or len(content) < 200:
        paragraphs = soup.find_all('p')
        content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    
    # Clean up the content
    content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
    content = re.sub(r'[ \t]+', ' ', content)  # Normalize spaces
    
    return content.strip()

def get_blog_post(url):
    """
    Retrieve blog post content and metadata from a given URL.
    
    Args:
        url (str): URL of the blog post to retrieve
        
    Returns:
        dict: Result with status, content, and metadata or error message
    """
    try:
        logger.info(f"Retrieving blog post from: {url}")
        result = {}
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL provided")
        
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; BlogRetriever/1.0; +https://aws.amazon.com/)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        # Check for HTTP 200 status
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.reason}")
            # result.status = "failed"
            # result.message = f"HTTP {response.status_code}: {response.reason}"
            return {
                "status": "failed",
                "url": url,
                # "metadata": metadata,
                "message": f"HTTP {response.status_code}: {response.reason}",
                "retrieved_at": datetime.now().isoformat()
            }
        else:
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata and content
            metadata = extract_metadata(soup, url)
            content = extract_content(soup)
            print(metadata)

            if not content:
                raise Exception("No content could be extracted from the page")
            
            return {
                "status": "success",
                "url": url,
                "metadata": metadata,
                "message": url + "\n\n" + content,
                "retrieved_at": datetime.now().isoformat()
            }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve the blog post: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Blog retrieval error for {url}: {e}")
        return systemError

def main(url):
    """
    Main function to retrieve and display blog post content.
    
    Args:
        url (str): URL of the blog post to retrieve
        
    Returns:
        dict: Result with status, content, and metadata or error message
    """
    if not url:
        print("Error: URL is required")
        return {"status": "error", "message": "URL is required"}
    
    result = get_blog_post(url)
    
    if result["status"] == "success":
        print(f"URL: {result['url']}")
        print(f"Tags: {', '.join(result['metadata']['tags'])}")
        print(" " * 50)
        print("Content Preview:")
        print(result['message'])
    else:
        print(f"Error: {result['message']}")
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Retrieve blog post content and metadata from a URL')
    parser.add_argument('url', help='URL of the blog post to retrieve')
    args = parser.parse_args()
    
    result = main(args.url)
    exit(0 if result["status"] == "success" else 1)
