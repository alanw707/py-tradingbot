import requests
from requests.auth import HTTPBasicAuth

class TradeOgre:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://tradeogre.com/api/v1'

    def get_balance(self, currency):
        url = f"{self.base_url}/private/balance"
        response = requests.get(url, auth=HTTPBasicAuth(self.api_key, self.secret_key))
        data = response.json()
        return data.get(currency.upper(), 0)

    def get_ticker(self, market):
        url = f"{self.base_url}/ticker/{market}"
        response = requests.get(url)
        return response.json()

    def get_orderbook(self, market):
        url = f"{self.base_url}/orders/{market}"
        response = requests.get(url)
        return response.json()

    def buy_order(self, market, price, quantity):
        url = f"{self.base_url}/order/buy"
        payload = {
            'market': market,
            'price': price,
            'quantity': quantity
        }
        response = requests.post(url, data=payload, auth=HTTPBasicAuth(self.api_key, self.secret_key))
        return response.json()

    def sell_order(self, market, price, quantity):
        url = f"{self.base_url}/order/sell"
        payload = {
            'market': market,
            'price': price,
            'quantity': quantity
        }
        response = requests.post(url, data=payload, auth=HTTPBasicAuth(self.api_key, self.secret_key))
        return response.json()

    def get_order_history(self, market):
        url = f"{self.base_url}/account/order_history"
        payload = {
            'market': market
        }
        response = requests.post(url, data=payload, auth=HTTPBasicAuth(self.api_key, self.secret_key))
        return response.json()
