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

import boto3
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Default error response
systemError = {
    "status": "error",
    "message": "We are currently unable to send the email. Please try again later."
}

def send_email(recipient, subject, content, sender_email=None, aws_region=None):
    """
    Send an email using AWS SES with the provided content to a recipient.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Subject line of the email
        content (str): Email content/body
        sender_email (str): Sender's email address (from env if not provided)
        aws_region (str): AWS region for SES (from env if not provided)
        
    Returns:
        dict: Result with status and message
    """
    try:
        # Get configuration from environment variables if not provided
        sender_email = sender_email or os.getenv('SENDER_EMAIL')
        aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
        
        if not sender_email:
            raise ValueError("Sender email must be provided via SENDER_EMAIL environment variable or parameter")
        
        logger.info(f"Sending email via AWS SES to: {recipient}")
        
        # Create SES client
        ses_client = boto3.client('ses', region_name=aws_region)
        
        # Add timestamp to content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_body = f"""
{content}

---
This email was generated automatically on {timestamp} via AWS SES.
        """.strip()
        
        # Send email using SES
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': email_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        message_id = response['MessageId']
        logger.info(f"Email sent successfully to {recipient}, MessageId: {message_id}")
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {recipient}",
            "recipient": recipient,
            "subject": subject,
            "sent_at": timestamp,
            "message_id": message_id,
            "aws_region": aws_region
        }
        
    except NoCredentialsError as e:
        logger.error(f"AWS credentials not found: {e}")
        return {
            "status": "error",
            "message": "AWS credentials not configured. Please set up AWS credentials."
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS SES error ({error_code}): {error_message}")
        
        if error_code == 'MessageRejected':
            return {
                "status": "error",
                "message": f"Email rejected by SES: {error_message}. Check if sender email is verified."
            }
        elif error_code == 'SendingPausedException':
            return {
                "status": "error",
                "message": "SES sending is paused for your account. Contact AWS support."
            }
        else:
            return {
                "status": "error",
                "message": f"AWS SES error: {error_message}"
            }
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return systemError
def send_email_html(recipient, subject, html_content, text_content=None, sender_email=None, aws_region=None):
    """
    Send an HTML email using AWS SES with the provided content to a recipient.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Subject line of the email
        html_content (str): HTML email content/body
        text_content (str): Plain text version (optional, will be generated if not provided)
        sender_email (str): Sender's email address (from env if not provided)
        aws_region (str): AWS region for SES (from env if not provided)
        
    Returns:
        dict: Result with status and message
    """
    try:
        # Get configuration from environment variables if not provided
        sender_email = sender_email or os.getenv('SENDER_EMAIL')
        aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
        
        if not sender_email:
            raise ValueError("Sender email must be provided via SENDER_EMAIL environment variable or parameter")
        
        logger.info(f"Sending HTML email via AWS SES to: {recipient}")
        
        # Create SES client
        ses_client = boto3.client('ses', region_name=aws_region)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare HTML content
        html_body = f"""
{html_content}
<hr>
<p><small>This email was generated automatically on {timestamp} via AWS SES.</small></p>
        """.strip()
        
        # Generate text version if not provided
        if not text_content:
            # Simple HTML to text conversion
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = f"{text_content}\n\n---\nThis email was generated automatically on {timestamp} via AWS SES."
        
        # Send email using SES
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_content,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        message_id = response['MessageId']
        logger.info(f"HTML email sent successfully to {recipient}, MessageId: {message_id}")
        
        return {
            "status": "success",
            "message": f"HTML email sent successfully to {recipient}",
            "recipient": recipient,
            "subject": subject,
            "sent_at": timestamp,
            "message_id": message_id,
            "aws_region": aws_region
        }
        
    except Exception as e:
        logger.error(f"HTML email sending error: {e}")
        return systemError

def send_agent_summary(recipient, summary_content, subject=None, format_html=False):
    """
    Send an email with agent summary content to a recipient.
    
    Args:
        recipient (str): Email address of the recipient
        summary_content (str): The summarized output from the agent
        subject (str): Custom subject line (optional)
        format_html (bool): Whether to format as HTML email (default: False)
        
    Returns:
        dict: Result with status and message
    """
    try:
        # Default subject if not provided
        if not subject:
            subject = f"Agent Summary Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        logger.info(f"Sending agent summary to: {recipient}")
        
        if format_html:
            # Format the content as HTML
            html_content = f"""
            <html>
            <body>
                <h2>Agent Summary Report</h2>
                <div style="border-left: 4px solid #007dbc; padding-left: 20px; margin: 20px 0;">
                    <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{summary_content}</pre>
                </div>
                <p><em>This summary was generated by your AI agent and contains the latest information and analysis.</em></p>
            </body>
            </html>
            """
            result = send_email_html(recipient, subject, html_content)
        else:
            # Format the content as plain text
            formatted_content = f"""
Agent Summary Report
====================

{summary_content}

This summary was generated by your AI agent and contains the latest information and analysis.
            """.strip()
            
            result = send_email(recipient, subject, formatted_content)
        
        return result
        
    except Exception as e:
        logger.error(f"Agent summary email error: {e}")
        return systemError

def main(recipient, content, subject=None, html=False):
    """
    Main function to send email with content using AWS SES.
    
    Args:
        recipient (str): Email address of the recipient
        content (str): Email content to send
        subject (str): Email subject (optional)
        html (bool): Whether to send as HTML email (default: False)
        
    Returns:
        dict: Result with status and message
    """
    if not recipient:
        print("Error: Recipient email address is required")
        return {"status": "error", "message": "Recipient email address is required"}
    
    if not content:
        print("Error: Email content is required")
        return {"status": "error", "message": "Email content is required"}
    
    # Default subject if not provided
    if not subject:
        subject = f"Automated Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    if html:
        result = send_email_html(recipient, subject, content)
    else:
        result = send_email(recipient, subject, content)
    
    if result["status"] == "success":
        print(f"Email sent successfully to: {recipient}")
        print(f"Subject: {subject}")
        print(f"Sent at: {result['sent_at']}")
        print(f"Message ID: {result['message_id']}")
        print(f"AWS Region: {result['aws_region']}")
    else:
        print(f"Error: {result['message']}")
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send email with content to a recipient using AWS SES')
    parser.add_argument('recipient', help='Email address of the recipient')
    parser.add_argument('content', help='Email content to send')
    parser.add_argument('--subject', help='Email subject line (optional)')
    parser.add_argument('--html', action='store_true', help='Send as HTML email')
    args = parser.parse_args()
    
    result = main(args.recipient, args.content, args.subject, args.html)
    exit(0 if result["status"] == "success" else 1)
