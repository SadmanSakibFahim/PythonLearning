from __future__ import annotations

import os
import time
import traceback
from typing import Iterable, List

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import AppConfig, PageConfig, PageField, Selector


def _by(selector: Selector):
    if selector.type == "css":
        return By.CSS_SELECTOR, selector.value
    if selector.type == "xpath":
        return By.XPATH, selector.value
    raise ValueError(f"Unsupported selector type: {selector.type}")


def _scroll_into_view(driver: WebDriver, element) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)


def _highlight(driver: WebDriver, element) -> None:
    driver.execute_script("arguments[0].style.outline='3px solid #ff0000';", element)


def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def capture_page_fields(driver: WebDriver, config: AppConfig, page: PageConfig, patient_id: str, output_dir: str) -> None:
    url = page.url_template.format(patient_id=patient_id)
    driver.get(url)

    if page.ready_selector:
        WebDriverWait(driver, config.default_timeout_seconds).until(
            EC.presence_of_element_located(_by(page.ready_selector))
        )

    if page.iframe:
        try:
            WebDriverWait(driver, config.default_timeout_seconds).until(
                EC.frame_to_be_available_and_switch_to_it(_by(page.iframe))
            )
        except Exception:
            # Try locating the iframe element directly and switch
            iframe_el = WebDriverWait(driver, config.default_timeout_seconds).until(
                EC.presence_of_element_located(_by(page.iframe))
            )
            driver.switch_to.frame(iframe_el)

    page_output_dir = os.path.join(output_dir, str(patient_id), page.key)
    _ensure_dir(page_output_dir)

    # Save page source for debugging
    with open(os.path.join(page_output_dir, "page_source.html"), "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    for field in page.fields:
        target_path = os.path.join(page_output_dir, f"{_safe_filename(field.name)}.png")
        try:
            by = _by(field.selector)
            element = WebDriverWait(driver, config.default_timeout_seconds).until(
                EC.presence_of_element_located(by)
            )
            _scroll_into_view(driver, element)
            time.sleep(0.2)
            _highlight(driver, element)
            element.screenshot(target_path)
        except Exception as e:
            err_path = os.path.join(page_output_dir, f"{_safe_filename(field.name)}.error.txt")
            with open(err_path, "w", encoding="utf-8") as ef:
                ef.write(f"Error capturing field '{field.name}': {e}\n\n")
                ef.write(traceback.format_exc())

    # Leave any iframes
    try:
        driver.switch_to.default_content()
    except Exception:
        pass


def capture_patient(driver: WebDriver, config: AppConfig, patient_id: str, output_dir: str, page_keys: List[str] | None) -> None:
    pages = config.patients.pages
    if page_keys:
        pages = [p for p in pages if p.key in set(page_keys)]
    for page in pages:
        capture_page_fields(driver, config, page, patient_id, output_dir)