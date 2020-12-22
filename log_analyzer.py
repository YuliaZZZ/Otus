#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from decimal import *
import json
import gzip
import logging
import os.path
import re
from json import JSONDecodeError
from statistics import median
from string import Template


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./fixtures/test_log"
}


def setup_logger(logfile=None):
    FORMAT = '[%(asctime)s] %(levelname)1s %(message)s'
    logging.basicConfig(format=FORMAT, filename=logfile,
                        datefmt='%Y.%m.%d %H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    return logger


def read_config(file_name):
    try:
        with open(file_name) as f:
            config = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(e)
    except JSONDecodeError as e:
        raise TypeError(e)
    else:
        return config


def search_log(log_dir):
    name_log = re.compile(
        r"^nginx-access-ui\.log-\d{8}(\.gz|)$"
    )
    log_list = list(filter(lambda x: re.fullmatch(name_log, x),
                           os.listdir(log_dir)))
    current_date = 0
    current_date_log = None

    for f in log_list:
        e_date = re.search(r'\d{8}', f).group(0)
        if int(e_date) > int(current_date):
            current_date = e_date
            current_date_log = f
    if current_date == 0:
        return current_date
    return {'name_log': current_date_log,
            'current_date': [current_date[:4],
                             current_date[4:6],
                             current_date[6:]]}


def open_log(filemame):
    if filemame.endswith('.gz'):
        file = gzip.open(filemame, 'rb')
    else:
        file = open(filemame)
    for line in file:
        yield line
    file.close()


def parser_line(lines, logger):
    error_count = 0
    lines_count = 0
    template = re.compile(
        r'^\S* \S*  - \[.+\] "\S* (\S*) HT.+" (\d{3}) .* (\S*)$')
    for line in lines:
        matches = re.search(template, line)
        if matches and matches.group(2) == "200":
            lines_count += 1
            yield matches.group(1), matches.group(3)
        else:
            error_count += 1
    if error_count > (lines_count // 2):
        logger.error("Лог невозможно проанализировать.")
        raise AssertionError("Лог невозможно проанализировать.")


def gen_data(data):
    new_data = {}
    for i in data:
        request, request_time = i
        if request not in new_data:
            new_data[request] = list()
        new_data[request].append(request_time)
    return new_data


def statistics_count(data):
    data = {k: [Decimal(i) for i in v] for k, v in data.items()}
    new_data = []
    count_perc = 0
    time_perc = 0
    for k, v in data.items():
        element = {"url": k, "count": len(data[k])}
        sorted(v)
        element['count'] = len(data[k])
        element['time_sum'] = round(float(sum(data[k])), 3)
        element['time_max'] = round(float(max(data[k])), 3)
        element['time_avg'] = round(float(sum(data[k]) / 2), 3)
        element['time_med'] = round(float(median(data[k])), 3)
        count_perc += element['count']
        time_perc += element['time_sum']
        new_data.append(element.copy())
    for i in new_data:
        i.update({'count_perc': round(float((i['count'] * 100) / count_perc), 3),
                  'time_perc': round(float((i['time_sum'] * 100) / time_perc), 3)})
    return new_data


def render_reports(table_data, report_name, logger):
    with open('report.html', 'r') as f:
        s = Template(f.read())
    with open(report_name, 'w') as fj:
        fj.write(s.safe_substitute(table_json=table_data))
    logger.info("Report is done.")


def main():
    parser = argparse.ArgumentParser(
        description='Log analyzer')
    parser.add_argument(
        '-conf', '--config',
        default={}, help='set config date')
    args = parser.parse_args()

    name_log_file = None

    conf = config

    if args.config:
        conf.update(read_config(args.config))

    if 'LOG_PATH' in conf:
        name_log_file = conf['LOG_PATH']

    logger = setup_logger(name_log_file)

    try:
        current_date = search_log(conf["LOG_DIR"])

        if current_date:
            report_name = conf["REPORT_DIR"] + f'/report-{".".join(current_date["current_date"])}.html'
            if not os.path.exists(report_name):
                log_file = conf["LOG_DIR"] + f'/{current_date["name_log"]}'
                lines = open_log(log_file)
                unparsed_data = parser_line(lines, logger)
                data = gen_data(unparsed_data)
                table = statistics_count(data)
                render_reports(table, report_name, logger)
        print('Done.')
    except (AssertionError, FileNotFoundError) as e:
        raise Exception(e)
    except (Exception, KeyboardInterrupt) as e:
        logger.exception(f'{e}')
        raise Exception(e)


if __name__ == "__main__":
    main()
