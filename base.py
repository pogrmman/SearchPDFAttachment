### Standard Libraries ###
import functools
import imaplib
import smtplib
import ssl
import email
import base64
import io
import os
import re

### Third-Party Libraries ###
import PyPDF4

### Exception Classes ###
class ImapException(Exception):
    """Base exception class for IMAP errors

    This exception provides the command that had an issue and if the
    issue was due to command failure or an error.
    """
    
    def __init__(self, command = None, response = None):
        """Initalize the exception with a command and the response type

        Usage:
        __init__(command, response)
            command -- the name of the command that failed
            response -- the IMAP response, either "NO" or "BAD"
        """
        
        if not command:
            command = 'An unknown IMAP command'
        elif command:
            command = 'The IMAP command {}'.format(command)
        if not response:
            response = 'failed or raised an error'
        elif response == 'NO':
            response = 'failed with response "NO"'
        elif response == 'BAD':
            response = 'raised an error with response "BAD"'
        message = '{} {}'.format(command, response)
        super().__init__(message)
        
class ImapCommandFailedError(ImapException):
    """Exception class for IMAP commands that failed

    This exception is for IMAP commands that provoke the response "NO",
    indicating that the command failed.
    """
    
    def __init__(self, command = None):
        """Initalize the exception for a particular command
        
        Usage:
        __init__(command)
            command -- the name of the IMAP command that failed
        """
        
        super().__init__(command, 'NO')

class ImapCommandErroredError(ImapException):
    """Exception class for IMAP commands that provoke an error

    This exception is for IMAP commands that provoke the response "BAD",
    indicating that there was an error.
    """
    
    def __init__(self, command = None):
        """Initalize the exception for a particular command

        Usage:
        __init__(command)
            command -- the name of the IMAP command that failed
        """
        super().__init__(command, 'BAD')

### Decorators ### 
def try_IMAP_command(command):
    """Decorator that raises an error if the IMAP command has an issue"""
    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        response = command(*args, **kwargs)
        if response[0] == 'NO':
            raise ImapCommandFailedError(command.__name__)
        elif response[0] == 'BAD':
            raise ImapCommandErroredError(command.__name__)
        else:
            return response
    return wrapper

# Decorate IMAP4 methods
imaplib.IMAP4.starttls = try_IMAP_command(imaplib.IMAP4.starttls)
imaplib.IMAP4.select = try_IMAP_command(imaplib.IMAP4.select)
imaplib.IMAP4.search = try_IMAP_command(imaplib.IMAP4.search)
imaplib.IMAP4.fetch = try_IMAP_command(imaplib.IMAP4.fetch)
imaplib.IMAP4.close = try_IMAP_command(imaplib.IMAP4.close)
imaplib.IMAP4.logout = try_IMAP_command(imaplib.IMAP4.logout)

### Functions ###
def fetch_emails(connection, search_string = '(UNSEEN)'):
    """Fetch emails on a connection, specified by a search

    Usage:
    fetch_emails(connection[, search_string])
        connection -- an IMAP connection, which should be logged in and
                      pointed at a particular mailbox
        search_string -- an IMAP search string that specifies the
                         messages to be fetched from the connection. 
                         Defaults to "(UNSEEN)", which fetches unread emails.
    
    Returns a list of email.message objects
    """
    
    matching_emails = connection.search(None,search_string)[1]
    matching_emails = matching_emails[0].decode().split()
    messages = [connection.fetch(email, '(RFC822)') for email in
                matching_emails]
    messages = [email.message_from_bytes(msg[1][0][1]) for msg in messages]
    return messages

def extract_pdfs(email_list):
    """Extract pdfs from a list of emails

    Usage:
    extract_pdfs(email_list):
        email_list -- a list of email.message objects

    Returns a list of PyPDF4.PdfFileReader objects.
    """
    
    email_list = [msg.get_payload() for msg in email_list if msg.is_multipart()]
    pdfs = [msg.get_payload() for email in email_list for msg in email
            if msg.get_content_type() == 'application/pdf']
    pdfs = [PyPDF4.PdfFileReader(io.BytesIO(base64.b64decode(pdf)))
            for pdf in pdfs]
    return pdfs

def extract_text(pdf_list):
    """Extract text from a list of pdfs

    Usage:
    extract_text(pdf_list):
        pdf_list -- a list of PyPDF4.PdfFileReader objects
    
    Returns a list of lists of strings. Each list of strings is a list
    comprised of one string for each line of text on a pdf page.
    """
    
    pdf_pages = [pdf.getPage(i) for pdf in pdf_list
                 for i in range(0, pdf.getNumPages())]
    pdf_text = [page.extractText().split('\n') for page in pdf_pages]
    return pdf_text

def match(pdf_texts, pattern):
    """Extract strings matching a regex from a list of lists of strings

    Usage:
    match(texts, pattern):
       texts -- a list of lists of strings, to be searched by regex
       pattern -- the regex pattern to match

    Returns a list of strings from 'texts', each of which matches the
    regex 'pattern'.
    """
    
    return [line for page in pdf_texts for line in page
            if re.search(pattern, line)]

def write_email(filename, frm, to):
    """Create an EmailMessage object from a text file

    Usage:
    write_email(filename, from, to):
        filename -- the name of the text file containing the email
        from -- the address of the sender
        to -- the address of the recipient

    Returns an EmailMessage object using the contents of the text file.
    The text file has the subject on the first line, followed by a
    blank line, followed by the text of the email.
    """

    email_msg = email.message.EmailMessage()
    email_msg["From"] = frm
    email_msg["To"] = to
    with open(filename, "r", encoding = "utf-8") as f:
       email_text = f.read()
    email_text = email_text.split("\n")
    email_msg["Subject"] = email_text[0]
    text = "\n".join(email_text[1:])
    email_msg.set_content(text)
    return email_msg

### Main Entry Point ###
if __name__ == "__main__":
    # Read in environment variables
    HOST = os.environ['PYTHON_EMAIL_HOST'].strip("\"")
    IMAP_PORT = int(os.environ['PYTHON_IMAP_PORT'])
    SMTP_PORT = int(os.environ['PYTHON_SMTP_PORT'])
    USER = os.environ['PYTHON_EMAIL_USER'].strip("\"")
    PASSWD = os.environ['PYTHON_EMAIL_PASSWD'].strip("\"")
    INBOX = os.environ['PYTHON_EMAIL_INBOX'].strip("\"")
    PATTERN = os.environ['PYTHON_REGEX_PATTERN'].strip("\"")
    RECIPIENT = os.environ['PYTHON_EMAIL_RECIPIENT'].strip("\"")
    
    # Connect to host and download unseen emails
    print(f'Connecting to the IMAP server {HOST} at port {IMAP_PORT}')
    connection = imaplib.IMAP4(HOST, IMAP_PORT)
    connection.starttls(ssl.create_default_context())
    print(f'Authenticating as user {USER}')
    connection.login(USER, PASSWD)
    print(f'Selecting inbox {INBOX}')
    connection.select(INBOX)
    print('Fetching unread emails')
    emails = fetch_emails(connection, '(UNSEEN)')
    connection.close()
    print('Logging out!')
    connection.logout()

    if emails:
        # Find matching texts
        print('Finding any pdfs in unread emails')
        pdfs = extract_pdfs(emails)
        if pdfs:
            print('Extracting text from pdfs')
            pdf_texts = extract_text(pdfs)
            print(f'Attempting to match text to regex {PATTERN}')
            matches = match(pdf_texts, PATTERN)
            
            # If there are matches, send an email to a recipient
            if matches:
                print('Matches found!')
                email_msg = write_email("emailText.txt", USER, RECIPIENT)
                print(f'Connecting to SMTP server {HOST} at port {SMTP_PORT}')
                smtp_connection = smtplib.SMTP(HOST, SMTP_PORT)
                smtp_connection.starttls()
                print(f'Authenticating as user {USER}')
                smtp_connection.login(USER, PASSWD)
                print('Sending email')
                smtp_connection.send_message(email_msg)
                print('Logging off!')
                smtp_connection.quit()
            else:
                print('No matches found!')
        else:
            print('No PDFS found!')
    else:
        print(f'No unread emails in the inbox {INBOX}')
