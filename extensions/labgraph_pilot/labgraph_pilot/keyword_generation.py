# generate the list names from predefined urls
# sicpy, numpy, sklearn
import requests
from bs4 import BeautifulSoup

class KeywordGeneration:

    '''
    A class that generates lists of APIs for different categories 
    (hardware devices, signal processing, etc.)
    '''   
    def __init__(self) -> None:
        self.predefined_urls = ['https://docs.scipy.org/doc/scipy/reference/signal.html',
                                # 'https://numpy.org/doc/stable/reference/routines.ma.html',
                                # 'https://numpy.org/doc/stable/reference/routines.math.html',
                                # 'https://numpy.org/doc/1.24/reference/routines.html',
                                # 'https://scikit-learn.org/stable/modules/classes.html#module-sklearn.preprocessing',
                                ]
        self.signal_processing_apis = []
        self.numpy_apis = []
        self.sklearn_apis = []
    def get_html_from_urls(self):
        for url in self.predefined_urls:
            page = requests.get(url)
            soup = BeautifulSoup(page.text, features="lxml")

            keywords_elements = soup.find_all("tr")
            for keyword in keywords_elements:
                # TODO: extract the 'keyword'

test = KeywordGeneration()
test.get_html_from_urls()