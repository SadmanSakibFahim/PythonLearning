from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
import yaml


SelectorType = Literal["css", "xpath"]


@dataclass
class Selector:
    type: SelectorType
    value: str


@dataclass
class LoginConfig:
    url: str
    username_selector: Selector
    password_selector: Selector
    submit_selector: Selector
    post_login_wait_seconds: int = 5
    cookies_path: Optional[str] = None  # Optional path to JSON cookies file


@dataclass
class PageField:
    name: str
    selector: Selector


@dataclass
class PageConfig:
    key: str
    url_template: str  # e.g., https://.../patients/{patient_id}/profile
    iframe: Optional[Selector] = None
    ready_selector: Optional[Selector] = None  # wait for this before capturing
    fields: List[PageField] = dataclasses.field(default_factory=list)


@dataclass
class PatientsConfig:
    url_template: Optional[str] = None
    pages: List[PageConfig] = dataclasses.field(default_factory=list)


@dataclass
class AppConfig:
    base_url: str
    login: LoginConfig
    patients: PatientsConfig
    default_timeout_seconds: int = 20
    headless: bool = True


def _selector_from_dict(d: dict) -> Selector:
    sel_type = d.get("type")
    value = d.get("value")
    if sel_type not in ("css", "xpath"):
        raise ValueError(f"Unsupported selector type: {sel_type}")
    if not value:
        raise ValueError("Selector value is required")
    return Selector(type=sel_type, value=value)


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    login_raw = raw["login"]
    login = LoginConfig(
        url=login_raw["url"],
        username_selector=_selector_from_dict(login_raw["username_selector"]),
        password_selector=_selector_from_dict(login_raw["password_selector"]),
        submit_selector=_selector_from_dict(login_raw["submit_selector"]),
        post_login_wait_seconds=login_raw.get("post_login_wait_seconds", 5),
        cookies_path=login_raw.get("cookies_path"),
    )

    pages: List[PageConfig] = []
    for key, page_raw in (raw.get("patients", {}).get("pages", {}) or {}).items():
        fields: List[PageField] = []
        for field_key, field_sel in (page_raw.get("fields", {}) or {}).items():
            fields.append(PageField(name=field_key, selector=_selector_from_dict(field_sel)))
        pages.append(
            PageConfig(
                key=key,
                url_template=page_raw["url_template"],
                iframe=_selector_from_dict(page_raw["iframe"]) if page_raw.get("iframe") else None,
                ready_selector=_selector_from_dict(page_raw["ready_selector"]) if page_raw.get("ready_selector") else None,
                fields=fields,
            )
        )

    patients = PatientsConfig(
        url_template=(raw.get("patients", {}) or {}).get("url_template"),
        pages=pages,
    )

    return AppConfig(
        base_url=raw["base_url"],
        login=login,
        patients=patients,
        default_timeout_seconds=raw.get("default_timeout_seconds", 20),
        headless=raw.get("headless", True),
    )