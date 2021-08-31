# SearchPDFAttachment
This script checks an inbox over IMAP (using `starttls`) for unread emails.
If there are unread emails, it fetches them and checks to see if there are PDFs attached to it.
It checks any PDFs that are there with a regex. If there are matches, it uses SMTP to send an email to a desired recipient.

### Configuration
The script uses the following environment variables for configuration:

    PYTHON_EMAIL_HOST -- the server to use for both IMAP and SMTP
    PYTHON_IMAP_PORT -- the port to use for IMAP connections
    PYTHON_SMTP_PORT -- the port to use for SMTP connections
    PYTHON_EMAIL_USER -- the user to login with
    PYTHON_EMAIL_PASSWD -- the password to login with
    PYTHON_EMAIL_INBOX -- the specific inbox to check over IMAP
    PYTHON_REGEX_PATTERN -- the regex to check the PDFs for
    PYTHON_EMAIL_RECIPIENT -- the recipient for the automated email if the regex is matched
    
Additionally, the directory you're running `base.py` in should contain a file `emailText.txt`, which is formatted as follows:

    SUBJECT GOES HERE
    (NEWLINE)
    MESSAGE BODY
    MESSAGE BODY CONTINUED
    ...
