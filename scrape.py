from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
import requests
from lxml import html
import json
from datetime import datetime
from pytz import timezone

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

PERIOD1_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[1]/td[1]'
PERIOD2_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[2]/td[1]'
PERIOD3_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[3]/td[1]'
PERIOD4_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[4]/td[1]'
PERIOD5_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[6]/td[1]'
PERIOD6_SELECTOR = '//*[@id="page-wrapper"]/div[3]/div/div[2]/div/div/div[2]/div/table/tbody/tr[5]/td[1]'

DISTRICT = environ.get('ILLUMINATE_DISTRICT')

def main():
  session = requests.session()
  
  # Start session
  result = session.get('https://{0}.illuminatehc.com'.format(DISTRICT))

  form = {
    '_username': environ.get('ILLUMINATE_USERNAME'),
    '_password': environ.get('ILLUMINATE_PASSWORD')
  }

  result = session.post('https://{0}.illuminatehc.com/login_check'.format(DISTRICT), data=form)
  result.raise_for_status()

  # You need this for some reason, if you don't request it, you'll get logged out
  result = session.get('https://{0}.illuminatehc.com/student-path?login=1'.format(DISTRICT))
  result = session.get('https://{0}.illuminatehc.com/gradebooks'.format(DISTRICT))

  # Get all HTML
  gradebooks_html = html.fromstring(result.text)

  PERIOD1_GRADE = gradebooks_html.xpath(PERIOD1_SELECTOR)
  PERIOD1_GRADE = (PERIOD1_GRADE[0].text)[2:-1] # Starts off with 'A 105%', then strips it down to '105'
  PERIOD2_GRADE = gradebooks_html.xpath(PERIOD2_SELECTOR)
  PERIOD2_GRADE = (PERIOD2_GRADE[0].text)[2:-1]
  PERIOD3_GRADE = gradebooks_html.xpath(PERIOD3_SELECTOR)
  PERIOD3_GRADE = (PERIOD3_GRADE[0].text)[2:-1]
  PERIOD4_GRADE = gradebooks_html.xpath(PERIOD4_SELECTOR)
  PERIOD4_GRADE = (PERIOD4_GRADE[0].text)[2:-1]
  PERIOD5_GRADE = gradebooks_html.xpath(PERIOD5_SELECTOR)
  PERIOD5_GRADE = (PERIOD5_GRADE[0].text)[2:-1]
  PERIOD6_GRADE = gradebooks_html.xpath(PERIOD6_SELECTOR)
  PERIOD6_GRADE = (PERIOD6_GRADE[0].text)[2:-1]

  new_grades = {
    'PERIOD1': PERIOD1_GRADE,
    'PERIOD2': PERIOD2_GRADE,
    'PERIOD3': PERIOD3_GRADE,
    'PERIOD4': PERIOD4_GRADE,
    'PERIOD5': PERIOD5_GRADE,
    'PERIOD6': PERIOD6_GRADE
  }

  # If there is a decimal in the string, it converts it to float, if not, int
  for k, v in new_grades.items():
    if '.' in v:
      new_grades[k] = float(v)
    else:
      new_grades[k] = int(v)

  # Get old grades
  jsonbin_auth = {
    'authorization': environ.get('JSONBIN_TOKEN')
  }

  old_grades = requests.get('https://jsonbin.org/cmelone/grades', headers=jsonbin_auth)
  old_grades.raise_for_status()
  old_grades = json.loads(old_grades.text) # Convert it to a dict

  differences = {
    'PERIOD1': round((new_grades['PERIOD1'] - old_grades['PERIOD1']), 2), # Subtract the old grade from the new grade and round to 2 points
    'PERIOD2': round((new_grades['PERIOD2'] - old_grades['PERIOD2']), 2),
    'PERIOD3': round((new_grades['PERIOD3'] - old_grades['PERIOD3']), 2),
    'PERIOD4': round((new_grades['PERIOD4'] - old_grades['PERIOD4']), 2),
    'PERIOD5': round((new_grades['PERIOD5'] - old_grades['PERIOD5']), 2),
    'PERIOD6': round((new_grades['PERIOD6'] - old_grades['PERIOD6']), 2)
  }

  # If there is a positive difference, then add a plus sign, negative, minus, if there is no difference, the make it no difference
  for k, v in differences.items():
    if differences[k] > 0:
      differences[k] = '+{0}%'.format(v)
    elif differences[k] < 0: 
      differences[k] = '{0}%'.format(v)
    else:
      differences[k] = 'No difference'
  
  differences_exist = False 

  # Check every class for differences, and if there is one, then set differences_exist = True
  for k, v in differences.items():
    if differences[k] != 'No difference':
      differences_exist = True
      break

  alert_string = ''

  # If there is no difference, then contruct a string and add it to alert_string
  # Figure out how to deal with line breaks
  if differences['PERIOD1'] != 'No difference':
    alert_string = alert_string + 'AP World: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD1'], new_grades['PERIOD1'], differences['PERIOD1'])
  if differences['PERIOD2'] != 'No difference':
    alert_string = alert_string + 'PE: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD2'], new_grades['PERIOD2'], differences['PERIOD2'])
  if differences['PERIOD3'] != 'No difference':
    alert_string = alert_string + 'Math: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD3'], new_grades['PERIOD3'], differences['PERIOD3'])
  if differences['PERIOD4'] != 'No difference':
    alert_string = alert_string + 'English: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD4'], new_grades['PERIOD4'], differences['PERIOD4'])
  if differences['PERIOD5'] != 'No difference':
    alert_string = alert_string + 'SLA: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD5'], new_grades['PERIOD5'], differences['PERIOD5'])
  if differences['PERIOD6'] != 'No difference':
    alert_string = alert_string + 'Chemistry: {0}% → {1}% ({2})\n'.format(old_grades['PERIOD6'], new_grades['PERIOD6'], differences['PERIOD6'])

  # Checks if the last 2 characters of the string are a ')' and newline, and if they are (means there are differences), remove newline
  if alert_string[-2:] == ')\n':
    alert_string = alert_string[:-1]

  if differences_exist:
    post_data = {
      'token': environ.get('PUSHOVER_TOKEN'),
      'user': environ.get('PUSHOVER_USER'),
      'message': alert_string
    }

    # Send notification to pushover
    pushover_post = requests.post('https://api.pushover.net/1/messages.json', data=post_data)
    pushover_post.raise_for_status()

    new_grades['LAST_UPDATED'] = datetime.now(timezone('US/Pacific')).strftime('%D %r') # Add LAST_UPDATED key to dict
    new_grades_post = requests.post('https://jsonbin.org/cmelone/grades', data=json.dumps(new_grades), headers=jsonbin_auth)
    new_grades_post.raise_for_status()

    if pushover_post.status_code == requests.codes.ok:
      print('{0}: Notification sent successfully'.format(datetime.now(timezone('US/Pacific')).strftime('%D %r')))
  else:
    print('{0}: Grades have not changed'.format(datetime.now(timezone('US/Pacific')).strftime('%D %r')))
  
if __name__ == '__main__':
    main()