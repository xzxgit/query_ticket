# -*- coding: utf-8 -*-
"""Train tickets query from 12306

Usage:
    tickets <from> <to> <date>

Options:
    -h --help   show help message

"""

from docopt import docopt
import re
import requests
from pprint import pprint
from prettytable import PrettyTable

import stations

#import pdb
#pdb.set_trace()
url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.8955'
#req = requests.get(url, verify=False)
#stations = dict(re.findall(r'([\u4e00-\u9fa5]+)\|([A-Z]+)', req.text))
#stations = dict(zip(stations.keys(), stations.values()))
#pprint(stations)

def colored(color, text):
    table = {
        'red': '\033[0;37m',
        'green': '\033[0;31m',
        'nc': '\033[0m'
    }
    cv = table.get(color)
    nc = table.get('nc')

    return ''.join([cv, text, nc])

class Ticket(object):

    def __init__(self):
        self.price_url = ''
        self.data = []
        self.rows = []
        self.table = PrettyTable()
        self.table.field_names = ["车次", "起始站", "终点站", "车站","时间","历时","商务座",\
                             "一等座","二等座","高级软卧","软卧","硬卧 ",\
                              "软座 ","硬座","无座"]
    def get_information(self, cli):
        req = requests.get(cli.url[0], verify=False)
        self.rows = req.json()['data']['result']
        self.price_url = cli.url[1]

    def _get_price(self, url):
        req = requests.get(url, verify=False)
        price = req.json()['data']
        item = {}
        item['busseat'] = price.get('A9', '-')
        item['frseat'] = price.get('M', '-')
        item['scseat'] = price.get('0', '-')
        item['highsleeper'] = price.get('A6', '-')
        item['softsleeper'] = price.get('A4', '-')
        item['hardsleeper'] = price.get('A3', '-')
        item['softseat'] = price.get('A2', '-')
        item['hardseat'] = price.get('A1', '-')
        item['noseat'] = price.get('WZ', '-')
        return item

    def _analysis(self):
        for row_item in self.rows:
            data_item = {}
            row = row_item.split('|')
            data_item['softsleeper'] = row[23] or '-'
            data_item['softseat'] = row[24] or '-'
            data_item['noseat'] = row[26] or '-'
            data_item['hardsleeper'] = row[28] or '-'
            data_item['hardseat'] = row[29] or '-'
            data_item['scseat'] = row[30] or '-'
            data_item['frseat'] = row[31] or '-'
            data_item['busseat'] = row[32] or '-'
            data_item['gosleeper'] = row[33] or '-'
            data_item['highsleeper'] = row[21] or '-'
            data_item['train_code'] = row[3] or '-'
            data_item['start'] = stations.get_name(row[4])
            data_item['end'] = stations.get_name(row[5])
            data_item['fro'] = stations.get_name(row[6])
            data_item['to'] = stations.get_name(row[7])
            data_item['start_time'] = row[8] or '-'
            data_item['arr_time'] = row[9] or '-'
            data_item['spend_time'] = row[10] or '-'
            data_item['train_no'] = row[2]
            data_item['from_station_no'] = row[16]
            data_item['to_station_no'] = row[17]
            data_item['seat_types'] = row[35]
            data_item['train_date'] = '{}-{}-{}'.format(row[13][0:4], row[13][4:6], row[13][6:])
            url = self.price_url.format(train_no=row[2], from_station_no=row[16],
                                  to_station_no=row[17], seat_types=row[35],
                                  train_date=data_item['train_date'])
            data_item['price'] = self._get_price(url)
            self.data.append(data_item)

    def show(self):
        self._analysis()
        for row in self.data:
            self.table.add_row([row['train_code'],
                                row['start'],
                                row['end'],
                               '\n'.join([colored('green', row['fro']),
                                colored('red', row['to'])]),
                               '\n'.join([colored('green', row['start_time']),
                                colored('red', row['arr_time'])]),
                               row['spend_time'],

                               '\n'.join([colored('green', row['busseat']),
                                colored('red', row['price']['busseat'])]),

                               '\n'.join([colored('green', row['frseat']),
                                colored('red', row['price']['frseat'])]),

                               '\n'.join([colored('green', row['scseat']),
                               colored('red', row['price']['scseat'])]),
                               '\n'.join([colored('green', row['highsleeper']),
                               colored('red', row['price']['highsleeper'])]),

                               '\n'.join([colored('green', row['softsleeper']),
                               colored('red', row['price']['softsleeper'])]),
                               '\n'.join([colored('green', row['hardsleeper']),
                               colored('red', row['price']['hardsleeper'])]),
                               '\n'.join([colored('green', row['softseat']),
                               colored('red', row['price']['softseat'])]),

                               '\n'.join([colored('green', row['hardseat']),
                               colored('red', row['price']['hardseat'])]),
                               '\n'.join([colored('green', row['noseat']),
                               colored('red', row['price']['noseat'])]),
                               ])
        print(self.table)


class Cli(object):


    def __init__(self):
        self.ticket_url = ('https://kyfw.12306.cn/otn/leftTicket/query?'
                           'leftTicketDTO.train_date={date}'
                           '&leftTicketDTO.from_station={fro}'
                           '&leftTicketDTO.to_station={to}'
                            '&purpose_codes=ADULT')
        self.price_url = ('https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?'
                         'train_no={train_no}'
                          '&from_station_no={from_station_no}'
                          '&to_station_no={to_station_no}'
                          '&seat_types={seat_types}'
                          '&train_date={train_date}')

        self.arguements = docopt(__doc__, version='Tickets 1.0')
        self.fro = stations.get_telecode(self.arguements['<from>'])
        self.to= stations.get_telecode(self.arguements['<to>'])
        self.date = self.arguements['<date>']

    @property
    def url(self):
        return [self.ticket_url.format(date=self.date, fro=self.fro, to=self.to),
                self.price_url]

if __name__ == '__main__':
    cli = Cli()
    ticket = Ticket()
    ticket.get_information(cli)
    ticket.show()
