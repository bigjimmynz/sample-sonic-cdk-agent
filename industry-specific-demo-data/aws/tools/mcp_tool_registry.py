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
#sys.path.append(os.path.join(os.path.dirname(__file__), '../../industry-specific-demo-data/aws/tools'))
from . import whats_new_rss_reader
from . import blog_retriever
from . import email_sender
from datetime import datetime

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

# Blog Retriever Tool
@mcp_server.tool(
    name="getBlogPost",
    description="Retrieve blog post content and metadata from a given URL"
)
async def blog_retriever_tool(
    url: Annotated[str, Field(description="URL of the blog post to retrieve")]
) -> dict:
    """Retrieve blog post content and metadata from URL"""
    try:
        logger.info(f"Retrieving blog post from: {url}")
        results = blog_retriever.main(url)
        return results  
    except Exception as e:
        logger.error(f"Error in blog retriever: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

# Email Sender Tool
@mcp_server.tool(
    name="sendEmail",
    description="Send an email with content to a recipient using AWS SES"
)
async def email_sender_tool(
    recipient: Annotated[str, Field(description="Email address of the recipient")],
    content: Annotated[str, Field(description="Email content to send")],
    subject: Annotated[str, Field(description="Email subject line", default="")] = "",
    format_html: Annotated[bool, Field(description="Whether to format as HTML email", default=False)] = False
) -> dict:
    """Send email using AWS SES"""
    try:
        logger.info(f"Sending email to: {recipient}")
        if format_html:
            results = email_sender.send_email_html(
                recipient, 
                subject or f"Automated Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                content
            )
        else:
            results = email_sender.send_email(
                recipient, 
                subject or f"Automated Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                content
            )
        return results  
    except Exception as e:
        logger.error(f"Error in email sender: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

# Agent Summary Email Tool
@mcp_server.tool(
    name="sendAgentSummary",
    description="Send an email with agent summary content to a recipient using AWS SES"
)
async def agent_summary_email_tool(
    recipient: Annotated[str, Field(description="Email address of the recipient")],
    summary_content: Annotated[str, Field(description="The summarized output from the agent")],
    subject: Annotated[str, Field(description="Custom email subject line", default="")] = "",
    format_html: Annotated[bool, Field(description="Whether to format as HTML email", default=False)] = False
) -> dict:
    """Send agent summary email using AWS SES"""
    try:
        logger.info(f"Sending agent summary email to: {recipient}")
        results = email_sender.send_agent_summary(recipient, summary_content, subject or None, format_html)
        return results  
    except Exception as e:
        logger.error(f"Error in agent summary email: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
