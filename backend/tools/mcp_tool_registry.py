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

# mcp_tool_registry.py
from typing import Annotated, Union
from pydantic import Field
from mcp_server import mcp_server
import logging
from . import knowledge_base_lookup
from . import retrieve_user_profile
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../industry-specific-demo-data/aws/tools'))
import whats_new_rss_reader

logger = logging.getLogger(__name__)

# Knowledge Base Lookup Tool
@mcp_server.tool(
    name="lookup",
    description="Runs query against a knowledge base to retrieve information."
)
async def lookup_tool(
    query: Annotated[str, Field(description="the query to search")]
) -> dict:
    """Look up information in the knowledge base"""
    try:
        logger.info(f"Knowledge base lookup query: {query}")
        results = knowledge_base_lookup.main(query)
        return results  
    except Exception as e:
        logger.error(f"Error in knowledge base lookup: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

# User Profile Search Tool
@mcp_server.tool(
    name="userProfileSearch",
    description="Search for a user's account and phone plan information by phone number"
)
async def user_profile_search_tool(
    phone_number: Annotated[Union[int, str], Field(description="the user's phone number")]
) -> dict:
    """Search for user profile and account information"""
    try:
        phone_str = str(phone_number)
        # logger.info(f"User profile search for: {phone_str}")
        results = retrieve_user_profile.main(phone_str)
        return results  
    except Exception as e:
        logger.error(f"Error in user profile search: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

# AWS What's New RSS Reader Tool
@mcp_server.tool(
    name="getWhatsNewEntries",
    description="Retrieve recent AWS What's New announcements from the RSS feed"
)
async def whats_new_rss_reader_tool(
    days: Annotated[int, Field(description="Number of days back to retrieve entries (default: 7)", default=7)]
) -> dict:
    """Retrieve AWS What's New RSS feed entries"""
    try:
        logger.info(f"Fetching AWS What's New entries for last {days} days")
        results = whats_new_rss_reader.get_rss_entries(days)
        return results  
    except Exception as e:
        logger.error(f"Error in AWS What's New RSS reader: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
