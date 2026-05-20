"""
enrich_products.py v2 — парсит maxmaster.ru через requests+BeautifulSoup
Вытаскивает: картинку, описание, преимущества, характеристики, комплектацию, габариты
"""
import argparse
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Product

DATABASE_URL = f"sqlite:///{Path(__file__).parent / 'toolprime.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

def get_canonical_url(url: str) -> str:
    """Убирает -ru-NNN суффикс из URL для получения канонического адреса."""
    return re.sub(r'-ru-\d+/?$', '/', url)

def fetch(url: str) -> str | None:
    try:
        r = SESSION.get(url, timeout=15, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def parse_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "image_url":     None,
        "description":   None,
        "features":      None,
        "complectation": None,
    }

    # ── Картинка ──────────────────────────────────────────────────────────────
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        result["image_url"] = og_img["content"].strip()

    # ── Описание (блок ОПИСАНИЕ) ──────────────────────────────────────────────
    desc_block = None
    for h in soup.find_all(["h3", "h4", "div", "p"], string=re.compile("ОПИСАНИЕ", re.I)):
        desc_block = h.find_next(["p", "div"])
        if desc_block and len(desc_block.get_text(strip=True)) > 30:
            break
    if not desc_block:
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            result["description"] = og_desc["content"].strip()[:1500]
    else:
        result["description"] = desc_block.get_text(" ", strip=True)[:1500]

    # ── Характеристики ────────────────────────────────────────────────────────
    features_lines = []

    # Вариант 1: таблица после заголовка ХАРАКТЕРИСТИКИ
    for header in soup.find_all(string=re.compile("ХАРАКТЕРИСТИК", re.I)):
        parent = header.parent
        # Ищем следующую таблицу или список рядом
        table = parent.find_next("table")
        if table:
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        features_lines.append(f"{key}: {val}")
            break

    # Вариант 2: dl списки
    if not features_lines:
        for dl in soup.find_all("dl"):
            for dt in dl.find_all("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    features_lines.append(f"{dt.get_text(strip=True)}: {dd.get_text(strip=True)}")

    # Вариант 3: ячейки с классами feature
    if not features_lines:
        for row in soup.select(".ty-product-feature, .feature-row, [class*=feature] tr"):
            cells = row.find_all(["td", "th", "span"])
            if len(cells) >= 2:
                features_lines.append(f"{cells[0].get_text(strip=True)}: {cells[1].get_text(strip=True)}")

    if features_lines:
        result["features"] = "\n".join(features_lines[:50])

    # ── Комплектация ──────────────────────────────────────────────────────────
    for header in soup.find_all(string=re.compile("КОМПЛЕКТ", re.I)):
        parent = header.parent
        # Ищем ul/ol/p после заголовка
        next_el = parent.find_next(["ul", "ol", "p", "div"])
        if next_el:
            items = next_el.find_all("li")
            if items:
                result["complectation"] = "\n".join(
                    f"• {li.get_text(strip=True)}" for li in items
                )[:1000]
            else:
                text = next_el.get_text(" ", strip=True)
                if len(text) > 5:
                    result["complectation"] = text[:1000]
            break

    return result


def process(product_id: int, url: str):
    canon = get_canonical_url(url)
    html = fetch(canon)
    if not html:
        html = fetch(url)  # fallback на оригинальный URL
    if not html:
        return product_id, None
    return product_id, parse_page(html)


def run(limit: int = None, workers: int = 5, reparse: bool = False):
    with Session(engine) as db:
        q = db.query(Product).filter(Product.source_url != None)
        if not reparse:
            q = q.filter(Product.features == None)
        if limit:
            q = q.limit(limit)
        products = [(p.id, p.source_url) for p in q.all()]

    total = len(products)
    print(f"\n  Товаров для обогащения: {total}")
    if total == 0:
        print("  Готово! Используйте --reparse для повторного парсинга.")
        return

    done = errors = updated = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process, pid, url): pid for pid, url in products}
        for future in as_completed(futures):
            pid, data = future.result()
            done += 1

            if data and any(v for v in data.values()):
                with Session(engine) as db:
                    p = db.get(Product, pid)
                    if p:
                        if data["image_url"]     and not p.image_url:     p.image_url     = data["image_url"]
                        if data["description"]   and not p.description:   p.description   = data["description"]
                        if data["features"]:      p.features      = data["features"]
                        if data["complectation"]: p.complectation = data["complectation"]
                        db.commit()
                        updated += 1
            else:
                errors += 1

            if done % 50 == 0 or done == total:
                elapsed = time.time() - start
                speed   = done / elapsed if elapsed > 0 else 0
                eta     = (total - done) / speed if speed > 0 else 0
                print(f"  [{done:>5}/{total}]  {speed:.1f} т/с  ETA {eta:.0f}с  обновлено: {updated}  ошибок: {errors}", flush=True)

    elapsed = time.time() - start
    print(f"\n  Готово за {elapsed:.0f}с")
    print(f"  Обновлено: {updated}  /  Ошибок: {errors}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int, default=None)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--reparse", action="store_true", help="Перепарсить все товары")
    args = parser.parse_args()
    run(args.limit, args.workers, args.reparse)
