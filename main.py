import requests
import xml.etree.ElementTree as ET
import os
import time
import sys
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_robots(robots_url, user_agent):
    """Fetch and parse robots.txt to check allowed URLs."""
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        print(f"[ERROR] Failed to read robots.txt: {e}")
    return rp


def is_allowed(rp, url, user_agent):
    """Check if a URL is allowed based on robots.txt."""
    return rp.can_fetch(user_agent, url)


def fetch_sitemap(sitemap_url, headers):
    """Fetch and parse the sitemap.xml file."""
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch sitemap: {e}")
        return None


def detect_encoding(content):
    """Detect the encoding of the content and decode properly."""
    detection = chardet.detect(content)
    encoding = detection.get("encoding", "utf-8")
    return content.decode(encoding, errors="ignore")


def fetch_article(url, headers, rp, retries=3):
    """Fetch a single article and save it as an HTML file with error handling and retries."""
    if not is_allowed(rp, url, headers["User-Agent"]):
        print(f"[INFO] Skipping disallowed URL: {url}")
        return None

    for attempt in range(retries):
        try:
            parsed_url = urlparse(url)
            clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path

            article_response = requests.get(
                clean_url, headers=headers, timeout=10)
            article_response.raise_for_status()

            if "text/html" not in article_response.headers.get("Content-Type", ""):
                print(f"[WARNING] Skipped non-HTML content: {url}")
                return None

            decoded_html = detect_encoding(article_response.content)
            soup = BeautifulSoup(decoded_html, "html.parser")
            pretty_html = soup.prettify()

            file_name = parsed_url.path.strip("/").replace("/", "_") or "index"
            file_name = file_name + ".html"
            file_path = os.path.join("articles", file_name)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(pretty_html)

            print(f"[SUCCESS] Saved: {file_name}")
            return file_name
        except requests.RequestException as e:
            print(
                f"[ERROR] Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"[ERROR] Unexpected error processing {url}: {e}")
            break
    return None


def fetch_and_save_articles(urls, headers, rp, max_workers=10):
    """Fetch and save articles concurrently using ThreadPoolExecutor with error handling."""
    os.makedirs("articles", exist_ok=True)
    print("Fetching accessible pages in parallel:")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(
            fetch_article, url, headers, rp): url for url in urls}

        for future in as_completed(future_to_url):
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Exception during parallel fetching: {e}")


def extract_main_content(soup):
    """Extract the main content and convert it to Markdown format."""
    content = []

    if soup.title:
        content.append(f"# {soup.title.get_text(strip=True)}\n")

    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "a", "strong", "em", "blockquote", "table", "tr", "th", "td", "img"]):
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            content.append(
                f"{'#' * int(element.name[1])} {element.get_text(strip=True)}\n")
        elif element.name == "p":
            content.append(f"{element.get_text(strip=True)}\n")
        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li"):
                content.append(f"- {li.get_text(strip=True)}")
        elif element.name == "a":
            link_text = element.get_text(strip=True)
            link_href = element.get("href", "")
            if link_href and not link_href.startswith("#"):
                content.append(f"[{link_text}]({link_href})")
        elif element.name == "strong":
            content.append(f"**{element.get_text(strip=True)}**")
        elif element.name == "em":
            content.append(f"*{element.get_text(strip=True)}*")
        elif element.name == "blockquote":
            content.append(f"> {element.get_text(strip=True)}")
    return "\n".join(content)


def convert_html_to_markdown():
    """Convert all HTML files in the 'articles' folder to Markdown format."""
    os.makedirs("texts", exist_ok=True)

    for file_name in os.listdir("articles"):
        if file_name.endswith(".html"):
            file_path = os.path.join("articles", file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    soup = BeautifulSoup(file, "html.parser")
                    extracted_text = extract_main_content(soup)
                text_file_path = os.path.join(
                    "texts", file_name.replace(".html", ".md"))
                with open(text_file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(extracted_text)
                print(f"[SUCCESS] Converted: {file_name} -> {text_file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to convert {file_name}: {e}")


def main_fetch(sitemap_url, robots_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    rp = fetch_robots(robots_url, headers["User-Agent"])
    response = fetch_sitemap(sitemap_url, headers)

    if response:
        try:
            root = ET.fromstring(response.content)
            namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [elem.text.strip()
                    for elem in root.findall(".//ns:loc", namespace)]
            fetch_and_save_articles(urls, headers, rp, max_workers=10)
        except ET.ParseError as e:
            print(f"[ERROR] Error parsing sitemap.xml: {e}")


def main_convert():
    convert_html_to_markdown()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <base_url>")
        sys.exit(1)

    base_url = sys.argv[1]
    sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml"
    robots_url = f"{base_url.rstrip('/')}/robots.txt"

    main_fetch(sitemap_url, robots_url)
    main_convert()
