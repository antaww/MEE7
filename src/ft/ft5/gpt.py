import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from loguru import logger

from src.ft.ft5.reports import Reports
from src.utilities.utilities import remove_non_bmp


class GPT:
    def __init__(self):
        reports = Reports()
        self.messages = reports.get_messages()
        # Load environment variables
        load_dotenv()
        self.email = os.getenv("GPT-EMAIL")
        self.password = os.getenv("GPT-PASSWORD")

        # Configure Chrome options for headless mode
        self.options = Options()
        self.options.add_argument("--start-maximized")

        # Initialize Chrome driver with undetected-chromedriver
        self.driver = uc.Chrome(options=self.options)

    def login(self):
        logger.info("Opening ChatGPT website...")
        self.driver.get("https://chatgpt.com/")

        logger.info("Waiting for login button to appear...")
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.find_element(By.XPATH, "//div[@id='__next']/div/div[2]/div/div/div/button"))
        time.sleep(1)  # Adding a short delay for security
        self.driver.find_element(By.XPATH, "//div[@id='__next']/div/div[2]/div/div/div/button").click()

        logger.info("Logging in with email...")
        WebDriverWait(self.driver, 10).until(lambda driver: driver.find_element(By.ID, "email-input"))
        self.driver.find_element(By.ID, "email-input").send_keys(self.email)
        self.driver.find_element(By.ID, "email-input").send_keys(Keys.ENTER)

        logger.info("Entering password...")
        WebDriverWait(self.driver, 10).until(lambda driver: driver.find_element(By.ID, "password"))
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        time.sleep(1)  # Adding a short delay for security
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

        logger.info("Waiting for prompt textarea to appear...")
        WebDriverWait(self.driver, 15).until(lambda driver: driver.find_element(By.ID, "prompt-textarea"))

    def send_prompt(self, prompt):
        logger.info("Writing prompt to ChatGPT...")
        textarea = self.driver.find_element(By.ID, "prompt-textarea")

        # Clear the textarea before sending the prompt
        textarea.clear()
        safe_prompt = remove_non_bmp(prompt)
        textarea.send_keys(safe_prompt)

        logger.debug("Security delay...")
        time.sleep(1)  # Adding a short delay for security

        # Simulate pressing Enter
        logger.info("Sending prompt...")
        textarea.send_keys(Keys.ENTER)

        logger.info("Waiting for response from ChatGPT...")
        time.sleep(1)  # Adding a short delay for response

        # Wait for the response, max 60s
        WebDriverWait(self.driver, 60).until(lambda driver: driver.find_element(By.CLASS_NAME, "icon-2xl"))

        # Get the inner text of the last div with class "markdown"
        time.sleep(10)  # Adding a short delay for response
        return self.driver.find_elements(By.CLASS_NAME, "markdown")[-1].text

    def close(self):
        logger.info("Closing Chrome driver...")
        try:
            self.driver.close()
        except Exception as e:
            logger.warning(f"An error occurred while closing the Chrome driver: {str(e)}")

    def generate_report_prompt(self, channel_name="general"):
        if not self.messages:
            return ""
        messages_text = self.generate_prompt_messages()
        moments_prompt = f"""
        The messages in the channel named `{channel_name}` are as follows: ----- {messages_text} ----- Identify and summarize the impactful moments from the conversation. This may include significant events, important discussions, strong viewpoints, emotions, or any other noteworthy points. Be precise and concise, your answer must contain at most 5 messages in a dot-point format, nothing more. The messages that you don't judge as "impactful" should not appear in the list. At the end of the list, please provide the global sentiment of the conversation with a really short sentence (positive, negative, neutral), example : "Global sentiment: positive, people are happy and excited about the new feature. Your complete answer must be written like this : [Message 1] "messagecontent" [Message 2] "messagecontent" [Same until 5 or less] "messagecontent" [Sentiment] "Global sentiment: sentiment_sentence" ---"
        """
        return moments_prompt.strip()

    def generate_activity_prompt(self, weather_datas, channel_name="general"):
        logger.info(f"Generating activity prompt for {weather_datas['city']}...")
        if not self.messages or not weather_datas:
            logger.error("No messages or weather data available to generate the prompt.")
            return ""
        messages_text = self.generate_prompt_messages()
        activity_prompt = f"""
        The messages in the channel named `{channel_name}` are as follows: ----- {messages_text} ----- Given the following weather conditions for {weather_datas['city']}: - Weather: {weather_datas['weather']} - Temperature: {weather_datas['temperature']}°C. Based on this information, please suggest at least 3 activities that are suitable for this weather. Ensure that the activities are appropriate for the conditions; for instance, if it is raining, suggest indoor activities, and if it is sunny and hot, avoid strenuous outdoor activities. Provide a mix of options such as restaurants, parks, museums, shopping, and sports, taking into account the comfort and safety of the participants. Your suggestions should be practical and relevant to the city mentioned. Here is the format for your response (do not send anything else than the json) : <br>```json ["""+"""{"activity": "Name of the activity","url": "https://relevanturl.com"},{"activity": "Name of the activity","url": "https://relevanturl.com"},{"activity": "Name of the activity","url": "https://relevanturl.com"}]```
        """
        return activity_prompt.strip()

    def generate_prompt_messages(self):
        extracted_messages = [message['content'].replace('\n', ' ') for message in self.messages]
        messages_text = ' '.join([f'"{message}"' for message in extracted_messages])
        logger.debug("Security delay...")
        time.sleep(1)  # Adding a short delay for security
        return messages_text
