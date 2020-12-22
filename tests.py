import os
import subprocess
import unittest

from log_analyzer import read_config, search_log, setup_logger


class LogAnalyzerTestCase(unittest.TestCase):
    def test_search_current_log(self):
        current_log = search_log('./fixtures/log')
        self.assertEqual(current_log["name_log"], 'nginx-access-ui.log-20200630')
        self.assertEqual(current_log["current_date"], ['2020', '06', '30'])

    def test_read_config(self):
        logger = setup_logger(logfile='log_otus')
        config = read_config(file_name='./fixtures/test_config.json')
        config_write = {"REPORT_SIZE": 1000,
                        "LOG_DIR": "./fixtures/log",
                        "REPORT_DIR": "./fixtures/test_reports"
                        }
        self.assertEqual(config, config_write)
        with self.assertRaises(TypeError):
            read_config(file_name='./fixtures/test_wrong_config')
        with self.assertRaises(FileNotFoundError):
            read_config(file_name='./fixtures/test_wrong')

    def test_analyzer_if_reports_already_exist(self):
        self.assertEqual(len(os.listdir('./fixtures/test_reports')), 1)
        subprocess.check_output(
            ["python3", "./log_analyzer.py", "-conf=fixtures/test_config.json"],
            universal_newlines=True,
        )
        self.assertEqual(len(os.listdir('./fixtures/test_reports')), 1)

    def test_analyzer_if_logs_not_exists(self):
        subprocess.check_output(
            ["python3", "./log_analyzer.py", "-conf=fixtures/test_config2.json"],
            universal_newlines=True,
        )
        self.assertEqual(len(os.listdir('./fixtures/reports')), 0)


