from email import message
import logging
from operator import sub
import os
from http.client import HTTPException, HTTPResponse
from typing import Any, Dict, List, Optional, Union

from python_http_client.exceptions import BadRequestsError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Attachment, Disposition, Email, FileContent,
                                   FileType, Mail, TemplateId, To, Subject,Cc,Content, Bcc)

sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
from base64 import b64encode

from celery import shared_task
import json


@shared_task(name='send_email')
def send_email(message: Dict[str,Any]) -> Union[HTTPResponse, BadRequestsError]:
    try:
        response = sendgrid_client.client.mail.send.post(request_body=message)
    except BadRequestsError as error:
        response = error
    log_message = f'SENDGRID EMAIL STATUS:{response.status_code}\nMail:\n{message}\n\nResponse:\n\n{response.body}'
    if response.status_code in [200, 201, 202]:
        logging.debug(log_message)
    else:
        logging.error(log_message)
    return None

def send_email_template(
    template_id: str,
    subject: str,
    to_emails: List[str],
    template_data:Optional[Dict[str,Any]] = {},
    files: Optional[List[Dict[bytes,str]]] = [],
    cc :Optional[List[str]] = [],
    bcc: Optional[List[str]] = []
) -> None:
    mail = create_email(to_emails, files, cc, bcc)
    if subject:
        mail.subject = Subject(subject)
   
    mail.template_id = TemplateId(template_id)
    mail.dynamic_template_data = template_data
  
    
    
   
    send_email.apply_async(args=[mail.get()],countdown=15)

def create_email( 
    to_emails: List[str],
    files: Optional[List[Dict[bytes,str]]] = [],
    cc :Optional[List[str]] = [],
    bcc: Optional[List[str]] = []
) -> Mail:
    from_email = Email('"Simplee Seguros" <contacto@simplee.cl>')
    to_email = [To(email) for email in to_emails]
    mail = Mail(from_email, to_email)
    mail.cc = [Cc(email) for email in cc]
    mail.bcc = [Bcc(email) for email in bcc]
    mail.attachment = [
        Attachment(
            file_content=FileContent(b64encode(file['file']).decode()),
            file_name=f'{file["filename"]}',
            file_type=FileType(file['type']),
            disposition=Disposition(),
        ) for file in files if all([file.get('filename'), file.get('file'), file.get('type')]) 
    ]
    
    return mail


def send_text_email(
    subject: str,
    to_emails: List[str],
    body:str,
    body_type='html',
    files: Optional[List[Dict[bytes,str]]] = [],
    cc :Optional[List[str]] = [],
    bcc :Optional[List[str]] = []
) -> None:
    message =  create_email(to_emails, files, cc, bcc)
    message.subject = Subject(subject)
    message_types = {
        'html':'text/html',
        'text':'text/plain'
    }
    message.content = [
        Content(
            mime_type=message_types.get(body_type,'hmtl'),
            content=body
        )
    ]
    send_email.apply_async(args=[message.get()],countdown=15)
