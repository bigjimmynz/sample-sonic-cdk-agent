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
import sys
import feedparser
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Default error response
systemError = {
    "status": "error",
    "message": "We are currently unable to retrieve the RSS feed. Please try again later."
}

def get_rss_entries(days=7):
    """
    Retrieves RSS feed entries from AWS What's New feed.
    
    Args:
        days (int): Number of days back to show entries
        
    Returns:
        dict: Result with status and entries or error message
    """
    try:
        logger.info(f"Fetching RSS feed entries for last {days} days")
        
        feed = feedparser.parse('https://aws.amazon.com/about-aws/whats-new/recent/feed/')
        if feed.bozo:
            raise Exception("Invalid RSS feed")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        # entries = {}
        entries = []
        entry_count = 0
        
        for entry in feed.entries:
            entry_date = datetime(*entry.published_parsed[:6])
            if entry_date >= cutoff_date:
                # entries[f"entry_{entry_count}"] = 
                object = {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published
                }
                entry_count += 1
                # entries = entries + "\n" + lines
                entries.append(object)
        
        response = {
            "status": "success",
            "entries": entries
        }
        
        return response
        
    except Exception as e:
        logger.exception(f"RSS feed error: {str(e)}")
        error = {"error": f"Unexpected error: {str(e)}"}
        print(json.dumps(error, indent=2))
        response = {"status": "error", "message": f"RSS feed error: {str(e)}"}
        return response

def main(days=7):
    """
    Main function to retrieve and display RSS feed entries.
    
    Args:
        days (int): Number of days back to show entries
        
    Returns:
        dict: Result with status and entries or error message
    """
    result = get_rss_entries(days)
    
    if result:
        logger.info(f"Found entries from the last {days} days:")
        logger.info(f"entries: {result}")
        # for entry_key, entry in result.items():
        #     print(f"Title: {entry['title']}")
        #     print(f"Link: {entry['link']}")
        #     print(f"Published: {entry['published']}")
        #     print(" " * 50)
        return result
    else:
        print(f"Error: {result['message']}")
        return result['message']
    
    # return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7, help='Number of days back to show entries (default: 7)')
    args = parser.parse_args()
    
    # result = main(args.days)
    sys.exit(main(args.days))
    # exit(0 if result["status"] == "success" else 1)
