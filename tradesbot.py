import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor


def get_vin(lot_link):
    lot_page = BeautifulSoup(requests.get(lot_link).text, 'lxml')
    lot_page_title = lot_page.find('title').text
    lot_page_description = \
        lot_page.find('div', class_='collapsible-body').find_all('span', class_='js-share-search')[-1].text
    try:
        vin_code = re.search(r'\b[(A-H|J-N|P|R-Z|0-9)]{17}\b', lot_page_title + lot_page_description).group(0)
    except:
        vin_code = ''
    return (vin_code)

titles = []
links = []
vin_codes = []
prices = []
lot_types = []
max_pages = 100
page = 0

# time markers
time_page = []


for page in range(max_pages):

    # begin page processing
    time_page.append(time.time())

    url = 'https://xn----etbpba5admdlad.xn--p1ai/search?regions%5B0%5D=77&trades-section=bankrupt&categorie_childs' \
          '%5B0%5D=2&page=' + str(page)
    raw = requests.get(url)

    soup = BeautifulSoup(raw.text, 'lxml')
    lots = soup.findAll('div', class_='lot-card')
    page_links = []

    if len(lots) != 0:
        print('processing page ' + str(page + 1) + '...')
        tcounter = 0

        for lot in lots:
            lot_title = lot.find('h3', class_='lot-description__title').find('a', class_='lot-description__link').text
            lot_link = lot.find('h3', class_='lot-description__title').find('a', class_='lot-description__link').get(
                'href')
            lot_price = lot.find('p', class_='price__text').text
            lot_type = lot.find('a', class_='js-bidding-step-open').get('data-tooltip')

            titles.append(lot_title.replace('\n', ''))
            links.append(lot_link)
            page_links.append(lot_link)
            prices.append(lot_price)
            lot_types.append(lot_type)

        with ThreadPoolExecutor(16) as executor:
            for result in executor.map(get_vin, page_links):
                vin_codes.append(result)
        executor.shutdown()

        time_page[page] -= time.time()
        time_page[page] = abs(time_page[page])

    else:
        time_page[page] -= time.time()
        time_page[page] = abs(time_page[page])
        break


# average time to process one page
import numpy
print(time_page)
print('avg page time ' + str(numpy.average(time_page)))

# creating dataframe
# lots_df = pandas.DataFrame(
#     {'title': titles,
#      'price': prices,
#      'link': links,
#      'type': lot_types,
#      'vin': vin_codes,
#      }
# )
#
# lots_df.to_csv(r'C:\Users\Adm\Documents\tradeparcer\lots', encoding='utf-8-sig')

# list of lists for google sheets
lots_list = []
for i in range(len(titles)):
    lots_list.append([titles[i], prices[i], links[i], lot_types[i], vin_codes[i]])

# exporting data to google sheets
import httplib2
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'tradesbot-366711-6c4339e84a44.json'
spreadsheet_id = '1NhMWsJ-BkPILhM8V3wLjIWN_DyJlVcOn_55a9TKrjWw'

# reading key from local file
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http())
from googleapiclient import discovery
service = discovery.build('sheets', 'v4', credentials=credentials)

# clearing the sheet
range_ = 'A1:Z1000'
clear_values_request_body = {

}
request = service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=range_, body=clear_values_request_body)
response = request.execute()

# writing data into the sheet
batch_update_values_request_body = {
    'value_input_option': 'USER_ENTERED',
    'data': [
        {'range': 'A:E',
         'majorDimension': 'ROWS',
         'values': lots_list,

         }
    ],
}
request = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)
response = request.execute()
