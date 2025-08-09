from __future__ import annotations

import json
import os
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

from .config import AppConfig, Selector


def _by(selector: Selector):
    if selector.type == "css":
        return By.CSS_SELECTOR, selector.value
    if selector.type == "xpath":
        return By.XPATH, selector.value
    raise ValueError(f"Unsupported selector type: {selector.type}")


def create_driver(config: AppConfig) -> webdriver.Chrome:
    load_dotenv()
    chrome_options = Options()
    headless_env = os.getenv("SELENIUM_HEADLESS")
    headless = config.headless if headless_env is None else headless_env not in ("0", "false", "False")
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1600,1200")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(max(10, config.default_timeout_seconds))
    return driver


def login_with_credentials(driver: webdriver.Chrome, config: AppConfig) -> None:
    username = os.getenv("WEBPT_USERNAME")
    password = os.getenv("WEBPT_PASSWORD")
    if not username or not password:
        raise RuntimeError("WEBPT_USERNAME and WEBPT_PASSWORD must be set in environment or .env file")

    driver.get(config.login.url)

    by_user = _by(config.login.username_selector)
    by_pass = _by(config.login.password_selector)
    by_submit = _by(config.login.submit_selector)

    WebDriverWait(driver, config.default_timeout_seconds).until(EC.presence_of_element_located(by_user))
    driver.find_element(*by_user).clear()
    driver.find_element(*by_user).send_keys(username)

    WebDriverWait(driver, config.default_timeout_seconds).until(EC.presence_of_element_located(by_pass))
    driver.find_element(*by_pass).clear()
    driver.find_element(*by_pass).send_keys(password)

    WebDriverWait(driver, config.default_timeout_seconds).until(EC.element_to_be_clickable(by_submit))
    driver.find_element(*by_submit).click()

    time.sleep(config.login.post_login_wait_seconds)


def apply_cookies_if_available(driver: webdriver.Chrome, config: AppConfig) -> bool:
    cookies_path = config.login.cookies_path
    if not cookies_path:
        return False
    try:
        driver.get(config.base_url)
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            cookie.pop("sameSite", None)  # selenium may not accept this field
            if "expiry" in cookie and isinstance(cookie["expiry"], float):
                cookie["expiry"] = int(cookie["expiry"])  # must be int
            driver.add_cookie(cookie)
        driver.get(config.base_url)
        return True
    except Exception:
        return False


def ensure_logged_in(driver: webdriver.Chrome, config: AppConfig) -> None:
    if not apply_cookies_if_available(driver, config):
        login_with_credentials(driver, config)