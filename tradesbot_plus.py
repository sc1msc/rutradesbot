import requests
import pandas
from bs4 import BeautifulSoup
import re
import ssl

titles = []
links = []
vin_codes = []
prices = []
lot_types = []
max_pages = 1
page = 1

for page in range(max_pages):

    print('processing page ' + str(page + 1) + '...')
    url = 'https://xn----etbpba5admdlad.xn--p1ai/search?regions%5B0%5D=77&trades-section=bankrupt&categorie_childs' \
          '%5B0%5D=2&page=' + str(page)
    raw = requests.get(url)

    soup = BeautifulSoup(raw.text, 'lxml')
    lots = soup.findAll('div', class_='lot-card')
    if len(lots) != 0:
        for lot in lots:
            lot_title = lot.find('h3', class_='lot-description__title').find('a', class_='lot-description__link').text
            lot_link = lot.find('h3', class_='lot-description__title').find('a', class_='lot-description__link').get(
                'href')
            lot_price = lot.find('p', class_='price__text').text
            lot_type = lot.find('a', class_='js-bidding-step-open').get('data-tooltip')
            # searching VIN at the lot page
            lot_page = BeautifulSoup(requests.get(lot_link).text, 'lxml')
            lot_page_title = lot_page.find('title').text
            lot_page_description = \
                lot_page.find('div', class_='collapsible-body').find_all('span', class_='js-share-search')[-1].text
            try:
                vin_code = re.search(r'\b[(A-H|J-N|P|R-Z|0-9)]{17}\b', lot_page_title + lot_page_description).group(0)
                titles.append(lot_title)
                links.append(lot_link)
                prices.append(lot_price)
                lot_types.append(lot_type)
                vin_codes.append(vin_code)
            except:
                titles.append(lot_title)
                links.append(lot_link)
                prices.append(lot_price)
                lot_types.append(lot_type)
                vin_codes.append(vin_code)

    else:
        break

# getting car info by VIN
AUTODOC = 'https://catalogoriginal.autodoc.ru/api/catalogs/original/cars/'
MODS = "/modifications"

def get_car_by_vin(vin):
    url = AUTODOC+vin+MODS
    ssl._create_default_https_context = ssl._create_unverified_context
    carbrand = ""
    carname = ""
    carproddate = ""
    caragg = ""
    try:
        res = requests.get(url)
        if res.status_code == 200:
            car = res.json()['commonAttributes']
            for elem in car:
                if elem['key'] == "Brand":
                    carbrand = elem['value']
                if elem['key'] == "Name":
                    carname = elem['value']
                if elem['key'] == "Date":
                    carproddate = elem['value']
                if elem['key'] == "aggregates":
                    caragg = elem['value']
    except AttributeError as err:
        print(err)
    return carbrand, carname, carproddate, caragg

car_make = []
car_model = []
car_year = []
car_info = []

for element in vin_codes:
    car_make.append(get_car_by_vin(element)[0])
    car_model.append(get_car_by_vin(element)[1])
    car_year.append(get_car_by_vin(element)[2])
    car_info.append(get_car_by_vin(element)[3])

# creating dataframe
lots_df = pandas.DataFrame(
    {'title': titles,
     'price': prices,
     'link': links,
     'type': lot_types,
     'vin': vin_codes,
     'make': car_make,
     'model': car_model,
     'year_produced': car_year,
     'info': car_info
     }
)

# print(lots_df.info)
# print(lots_df.head())
lots_df.to_csv(r'C:\Users\Adm\Documents\tradeparcer\lots_plus.csv', encoding='utf-8-sig')
