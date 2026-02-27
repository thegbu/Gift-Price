from typing import Dict, Optional
from bs4 import BeautifulSoup
import re
import logging

log = logging.getLogger(__name__)

GiftDetails = Dict[str, Optional[str]]


def parse_gift_page(html: str, link: str) -> GiftDetails:
    soup = BeautifulSoup(html, "html.parser")
    meta_title = soup.find("meta", property="og:title")
    title = meta_title["content"].strip() if meta_title else link
    gift_name_match = re.match(r"^(.*?)(?:\s*(?:#|-)\d+)?$", title)
    gift_name_clean = gift_name_match.group(1).strip() if gift_name_match else title

    details: GiftDetails = {
        "title": title,
        "gift_name_clean": gift_name_clean,
        "model_name": None, 
        "model_percent": None, 
        "backdrop_name": None,
        "backdrop_percent": None, 
        "symbol_name": None, 
        "symbol_percent": None
    }

    table = soup.find("table", class_="tgme_gift_table")
    rows = table.find_all("tr") if table else []

    for row in rows:
        key = row.find("th").get_text(strip=True).lower() if row.find("th") else ""
        td = row.find("td")
        if key and td:
            mark = td.find("mark")
            percent = mark.get_text(strip=True) if mark else None
            if mark: 
                mark.extract()
            value = td.get_text(strip=True)
            if key == "model": 
                details["model_name"], details["model_percent"] = value, percent
            elif key == "backdrop": 
                details["backdrop_name"], details["backdrop_percent"] = value, percent
            elif key == "symbol": 
                details["symbol_name"], details["symbol_percent"] = value, percent

    return details


def format_gift_details(gift_details: GiftDetails, link: str) -> str:
    output = f'🎁 <a href="{link}">{gift_details["title"]}</a>\n\n'
    
    if gift_details["model_name"]:
        output += f'- Model: <code>{gift_details["model_name"]}</code> ({gift_details["model_percent"]})\n'
    if gift_details["backdrop_name"]:
        output += f'- Backdrop: <code>{gift_details["backdrop_name"]}</code> ({gift_details["backdrop_percent"]})\n'
    if gift_details["symbol_name"]:
        output += f'- Symbol: <code>{gift_details["symbol_name"]}</code> ({gift_details["symbol_percent"]})'
    
    return output
