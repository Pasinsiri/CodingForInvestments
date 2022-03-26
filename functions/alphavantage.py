import requests 
import pandas as pd 
import csv 

class AlphaVantageReader():
    def __init__(self, key) -> None:
        self.key = key
        self.url_template = f'https://www.alphavantage.co/query?&apikey={self.key}&'

    def _load_and_decode(self, url:str) -> pd.DataFrame:
        """(helper) load CSV tables from AlphaVantage, decode and convert to Pandas' DataFrame

        Args:
            url (str): a full endpoint url

        Returns:
            pd.DataFrame: a cleaned DataFrame of data fetched from the API
        """
        with requests.Session() as s:
            download = s.get(url)
            decoded_content = download.content.decode('utf-8')
            cr = list(csv.reader(decoded_content.splitlines(), delimiter=','))
            df = pd.DataFrame(cr[1:], columns = cr[0])
        return df

    def get_company_data(self, function:str, symbol:str, mode:str = 'quarterly') -> pd.DataFrame:
        """get a company report with a specific period

        Args:
            function (str): report name, can be balance_sheet or cash_flow
            symbol (str): stock ticker
            mode (str, optional): period of interest, can be quarterly or annual. Defaults to 'quarterly'.

        Returns:
            pd.DataFrame: a dataframe contains data of the selected company
        """
        child_url = f'function={function.upper()}&symbol={symbol}'
        r = requests.get(self.url_template + child_url)
        data = r.json() 
        raw_df = data[mode + 'Reports']
        df = pd.concat([pd.Series(x) for x in raw_df], axis = 1).T.set_index('fiscalDateEnding')
        df.insert(0, 'symbol', [symbol] * df.shape[0])
        return df 

    def get_ticker_overview(self, symbol:str) -> pd.Series:
        """get overview information about a specific company

        Args:
            symbol (str): stock ticker

        Returns:
            pd.Series: a series contains overview information of the selected company
        """
        child_url = f'function=OVERVIEW&symbol={symbol}'
        r = requests.get(self.url_template + child_url)
        data = r.json() 
        return pd.Series(data)

    def get_listed_companies(self, is_active:bool = False) -> pd.DataFrame:
        """get all listed tickers

        Args:
            is_active (bool, optional): if true, only active tickers will be fetched, otherwise all tickers. Defaults to False.

        Returns:
            pd.DataFrame: a dataframe of every tickers (companies and ETFs) with its respective ticker, asset type, market, IPO date, delisting date (if any), and status flag
        """
        child_url = 'function=LISTING_STATUS'
        df = self._load_and_decode(self.url_template + child_url)
        if is_active:
            return df[df['status'] == 'active'].reset_index(drop = True) 
        else:
            return df 

    def get_earnings_calendar(self, ticker:str = None, horizon:str = '3month') -> pd.DataFrame:
        """get earnings calendar of every company

        Args:
            ticker (str, optional): if specified, only estimate earnings of the ticker will be selected, if not, estimate earnings of every company will be selected
            horizon (str, optional): future timespan of interest, can be 3month, 6month, or 12month. Defaults to '3month'.

        Returns:
            pd.DataFrame: a dataframe contains estimate earnings of every company
        """
        child_url = f'function=EARNINGS_CALENDAR&horizon={horizon}'
        df = self._load_and_decode(self.url_template + child_url)
        if ticker is None:
            return df
        else:
            return df[df['symbol'] == ticker]