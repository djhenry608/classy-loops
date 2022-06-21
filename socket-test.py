import requests

r = requests.post('http://127.0.0.1:8080/test', json={'param1': 'value1', 'param2': 'value2'})