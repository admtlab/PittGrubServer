import configparser
import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tornado.options import options

EMAIL_ADDRESS = None
EMAIL_USER = None
EMAIL_PASS = None
EMAIL_HOST = None
EMAIL_PORT = None
EMAIL_SENDER = "PittGrub Support"
EMAIL_SUBJECT = "PittGrub Account Verification"
VERIFICATION_ENDPOINT = "users/activate"
APPSTORE_LINK = 'https://appsto.re/us/dACI6.i'
PLAYSTORE_LINK = 'https://play.google.com/store/apps/details?id=host.exp.exponent'
EXPO_LINK = 'exp://exp.host/@admtlab/PittGrub'
TEXT = """\
Welcome to PittGrub!

Your verification code is: {code}

Next steps:
You're close to receiving free food! Just enter your activation code in the PittGrub app to verify your account.

If you don't have the PittGrub mobile app, follow these steps to install it:
1) Download the Expo Client app. It is available for iOS at {ios} and Android at {android}.
2) Install the PittGrub app in Expo with the following project link: {expo}. We currently support iOS, and Android support is coming soon.
    
PittGrub is growing quickly, and we approve users daily. We will notify you when you're account has been accepted.

Thanks for signing up,
PittGrub Team


If you've received this email in error, please reply with the details of the issue experienced.
"""
HTML = """\
<h2 align="center">Welcome to PittGrub!</h2>
    
Your verification code is: <b>{code}</b>.

<h3>Next steps</h3>
You're close to receiving free food! Just log in to the PittGrub app with your credentials and enter your verification code when prompted.

<br><br>
If you don't have the PittGrub mobile app, follow these steps to install it:
<ol>
    <li>Download the Expo Client app. It is available on both <a href='{ios}'>iOS</a> and <a href='{android}'>Android</a>. </li>
    <li>Install the PittGrub app in Expo with the following project link: <a href='{expo}'>{expo}</a>. We currently support iOS, and Android support is coming soon. </li>
</ol>

PittGrub is growing quickly, and we approve users daily. We will notify you when you're account has been accepted.
<br>
<br>
Thanks for signing up,
<br>
PittGrub Team

<br><br>
<p style="color:#aaaaaa;font-size:10px">If you've received this email in error, please reply with the details of the issue experienced.</p>
"""


def create_verification_code(length: int = 6) -> str:
    """
    Creates a verification code comprising upper case characters and digits
    :param length: length of code (default: 6)
    :return: code
    """
    chars = string.ascii_uppercase + string.digits
    code = random.choices(chars, k=length)
    return ''.join(code)


def __get_credentials() -> None:
    """
    Get email server credentials
    """
    global EMAIL_HOST, EMAIL_PORT, EMAIL_ADDRESS, EMAIL_USER, EMAIL_PASS
    config = configparser.ConfigParser()
    config.read(options.config)
    email_config = config['EMAIL']
    EMAIL_ADDRESS = email_config.get('address')
    EMAIL_USER = email_config.get('username')
    EMAIL_PASS = email_config.get('password')
    EMAIL_HOST = email_config.get('host')
    EMAIL_PORT = email_config.get('port')


def send_verification_email(to: str, code: str) -> bool:
    # verified server was created
    if not (EMAIL_ADDRESS or EMAIL_USER or EMAIL_PASS or EMAIL_HOST or EMAIL_PORT):
        __get_credentials()

    # setup server
    email_server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)

    # construct message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = f'{EMAIL_SENDER} <{EMAIL_ADDRESS}>'
    msg['To'] = to

    # body
    text_body = TEXT.format(code=code,
                            ios=APPSTORE_LINK,
                            android=PLAYSTORE_LINK,
                            expo=EXPO_LINK)
    html_body = HTML.format(code=code,
                            ios=APPSTORE_LINK,
                            android=PLAYSTORE_LINK,
                            expo=EXPO_LINK)
    msg.attach(MIMEText(text_body, 'text'))
    msg.attach(MIMEText(html_body, 'html'))

    # send message
    email_server.ehlo()
    email_server.starttls()
    email_server.login(EMAIL_USER, EMAIL_PASS)
    email_server.sendmail(msg['From'], msg['To'], msg.as_string())
    email_server.quit()
