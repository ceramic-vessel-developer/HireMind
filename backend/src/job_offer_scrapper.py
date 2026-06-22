import re
import time
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class AbstractScrapper(ABC):
    @abstractmethod
    def extract_text(self,url)-> str:
        pass



class BaseScrapperStrategy(AbstractScrapper):

    def __init__(self):
        self.driver = None

    def initialize_webdriver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)

    def extract_text(self,url:str) -> str:
        raise NotImplemented


class LinkedinScrapperStrategy(BaseScrapperStrategy):
    def __init__(self):
        super().__init__()

    def extract_text(self,url:str)-> str:
        self.initialize_webdriver()
        self.driver.get(url)
        raw_html = self._extract_offer_text()
        extracted_text = self._remove_html_tags(raw_html)
        self.driver.close()
        return extracted_text


    def _close_login_popup(self):
        popup_close = self.driver.find_element(By.XPATH, "/html/body/div[7]/div/div/section/button")
        popup_close.click()

    def _extract_offer_text(self)-> str:
        job_offer_text = self.driver.find_element(By.XPATH,
                                             "/html/body/main/section[1]/div/div/section[1]/div/div/section/div")
        text_extracted = job_offer_text.get_attribute("innerHTML")
        return text_extracted

    def _remove_html_tags(self,text: str) -> str:
        return re.sub(r'<[^>]+>', '', text)


class ScrapperStrategyFactory:
    scrapper_strategies = {
        "Linkedin":LinkedinScrapperStrategy(),
    }

    def get_scrapper(self):
        return self.scrapper_strategies.get("Linkedin")

if __name__=="__main__":
    # driver = webdriver.Firefox()
    # driver.get("http://www.python.org")
    # assert "Python" in driver.title
    # elem = driver.find_element(By.NAME, "q")
    # elem.clear()
    # elem.send_keys("pycon")
    # elem.send_keys(Keys.RETURN)
    # assert "No results found." not in driver.page_source
    # driver.close()
    scrapper = ScrapperStrategyFactory().get_scrapper()
    first_offer = scrapper.extract_text("https://mt.linkedin.com/jobs/view/junior-mid-full-stack-developer-ai-native-at-paradise-media-4400778383?trk=public_jobs_topcard-title")
    second_offer = scrapper.extract_text("https://mt.linkedin.com/jobs/view/bi-developer-at-payfuture-4399205799?trk=public_jobs_topcard-title")
    print(first_offer)
    print(second_offer)