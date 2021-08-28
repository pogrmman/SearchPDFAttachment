### Standard Libraries ###
import imaplib
import ssl
import email
import io
import base64
import re
import os

### Third-Party Libraries ###
import PyPDF4

# Read in environment variables
HOST = os.environ.get['PYTHON_EMAIL_HOST']
PORT = os.environ.get['PYTHON_EMAIL_PORT']
USER = os.environ.get['PYTHON_EMAIL_USER']
PASSWD = os.environ.get['PYTHON_EMAIL_PASSWD']
INBOX = os.environ.get['PYTHON_EMAIL_INBOX']
PATTERN = os.environ.get['PYTHON_REGEX_PATTERN']

# Download new emails in inbox
connection = imaplib.IMAP4(HOST, PORT)
connection.starttls(ssl.create_default_context())
connection.login(USER, PASSWD)
connection.select(INBOX)
return_val, unread_emails = connection.search(None, '(UNSEEN)')
if return_val == "OK":
    messages = [connection.fetch(email, '(RFC822)') for email in unread_emails[0].decode().split()]
connection.close()
connection.logout()

# Extract all pdfs
email_list = [email.message_from_bytes(msg[1][0][1]) for msg in messages]
payloads = [msg.get_payload() for msg in email_list if msg.is_multipart()]
pdfs = [payload.get_payload() for email in payloads
        for payload in email if payload.get_content_type() == 'application/pdf']
pdfs = [PyPDF4.PdfFileReader(io.BytesIO(base64.b64decode(pdf))) for pdf in pdfs]

# Get pages
pdf_pages = [pdf.getPage(i) for pdf in pdfs for i in range(0,pdf.getNumPages())]
pdf_page_texts = [page.extractText().split('\n') for page in pdf_pages]

# Find matches
results = [line for page in pdf_page_texts for line in page if re.search(PATTERN, line)]
