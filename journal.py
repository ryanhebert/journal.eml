import sys
import os
import shutil
import email
import smtplib
import dns.resolver
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE

path = sys.argv[1]
address = sys.argv[2]

def isIP(addr):
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False

def listdir(d):

    fileList = []
    path = os.path.join(os.path.dirname(__file__), d)

    if not os.path.isdir(path):
        print d
    else:
        for item in os.listdir(d):
            fileList.append(d + '\\' + item)

    return fileList

def journal_messages(path, address):

    messages = listdir(path)
    send_to = None

    if not isIP(address):

        send_to=[address]
        domain = address.split('@')[1]

        if isIP(domain):
            address = domain
        else:
            servers = dns.resolver.query(domain, 'MX')
            for s in servers:
                address = s.exchange
    
    count = 0
    smtp = smtplib.SMTP(str(address))

    for eml in messages:

        if not os.path.isdir(eml):

            if count % 20 == 0 and count > 0:
                smtp.close()
                print "\nresetting SMTP connection...\n"
                smtp = smtplib.SMTP(str(address))

            count += 1

            with open(eml, 'r') as myfile:
                archivedText = myfile.read()

            archivedMessage = email.message_from_string(archivedText)
            messageId = '@journal.report.generator'


            if 'From' in archivedMessage:
                send_from = archivedMessage['From']
            else:
                send_from="journaling@messages"

            if not send_to and 'To' in archivedMessage:
                send_to = [archivedMessage['To']]
            elif not send_to:
                send_to = ['journaling@messages']


            if 'Subject' in archivedMessage:
                subject = archivedMessage['Subject']
            else:
                subject = eml

            if 'Message-Id' in archivedMessage:
                ParentMessageId = archivedMessage['Message-Id']
            else:
                ParentMessageId = None

            #X-MS-Exchange-Parent-Message-Id: <CY4PR10MB1544419808D43882EFAE5C04F9300@CY4PR10MB1544.namprd10.prod.outlook.com>
            text = 'Sender: '+ str(send_from) + '\nSubject: ' + str(subject) + '\nMessage-Id: <' + str(messageId) + '>\nTo: ' + str(send_to) + '\n'

            msg = MIMEMultipart()
            msg['From'] = send_from
            msg['To'] = COMMASPACE.join(send_to)
            msg['Sender'] = 'journaling@messages'
            msg['Subject'] = subject
            msg['Message-ID'] = messageId
            msg['Parent-Message-Id'] = ParentMessageId
            msg['X-MS-Journal-Report'] = None

            msg.attach(MIMEText(text))
            msg.attach(MIMEText(archivedText))

            print eml
            response = smtp.sendmail(send_from, send_to, msg.as_string())

            if len(response) == 0:
                if not os.path.exists('journaled'):
                    os.makedirs('journaled')
                pth, fn = os.path.split(eml)
                #print pth
                shutil.move(eml, 'journaled')

    smtp.close()

journal_messages(path, address)