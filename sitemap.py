import requests
import xml.etree.ElementTree as ET
import os
import time
import sys
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
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


def detect_encoding(content):
    """Detect encoding of content and decode properly."""
    detection = chardet.detect(content)
    encoding = detection.get("encoding", "utf-8")
    return content.decode(encoding, errors="ignore")


def fetch_article(url, headers, rp, retries=3):
    """Fetch and save an article as an HTML file."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            if "text/html" not in response.headers.get("Content-Type", ""):
                print(f"[WARNING] Skipped non-HTML content: {url}")
                return None, None

            decoded_html = detect_encoding(response.content)
            soup = BeautifulSoup(decoded_html, "html.parser")
            file_name = urlparse(url).path.strip(
                "/").replace("/", "_") or "index"
            file_path = os.path.join("articles", f"{file_name}.html")

            os.makedirs("articles", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(soup.prettify())

            print(f"[SUCCESS] Saved: {url}")
            return file_name, soup
        except requests.RequestException as e:
            print(
                f"[ERROR] Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(2 ** attempt)
    return None, None


def normalize_url(url):
    """Normalize URL by removing fragmen."""
    parsed_url = urlparse(url)
    if parsed_url.path.endswith('/'):
        parsed_url = parsed_url._replace(path=parsed_url.path[:-1])
    return parsed_url._replace(fragment='').geturl()


def extract_links(base_url, rp, headers):
    """Recursively extract allowed links from the website cluster."""
    visited = set()
    to_visit = {normalize_url(base_url)}

    while to_visit:
        url = to_visit.pop()
        url = normalize_url(url)  # Normalize URL by removing fragment
        if url in visited:
            continue

        if urlparse(url).scheme != "https":
            print(f"[INFO] Skipped non-HTTPS URL: {url}")
            continue

        file_name, soup = fetch_article(url, headers, rp)
        if not soup:
            continue

        visited.add(url)

        links = {urljoin(url, link["href"])
                 for link in soup.find_all("a", href=True)}
        for link in links:
            normalized_link = normalize_url(link)  # Normalize link
            if urlparse(normalized_link).netloc == urlparse(base_url).netloc and rp.can_fetch(headers["User-Agent"], normalized_link):
                if normalized_link not in visited:
                    to_visit.add(normalized_link)

    return list(visited)


def determine_priority(url):
    """Determine priority based on URL depth."""
    return max(0.1, round(1.0 - 0.1 * urlparse(url).path.count("/"), 1))


def generate_sitemap(urls):
    """Generate sitemap.xml with better readability."""
    urlset = ET.Element(
        "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Sort by priority then by URL
    urls.sort(key=lambda x: (-determine_priority(x), x))

    for url in urls:
        url_element = ET.SubElement(urlset, "url")
        ET.SubElement(url_element, "loc").text = url
        ET.SubElement(url_element, "priority").text = str(
            determine_priority(url))

    sitemap_path = "sitemap.xml"
    tree = ET.ElementTree(urlset)

    with open(sitemap_path, "wb") as file:
        tree.write(file, encoding="utf-8", xml_declaration=True)

    with open(sitemap_path, "r", encoding="utf-8") as file:
        formatted_xml = "\n".join([line.strip() for line in file.readlines()])

    with open(sitemap_path, "w", encoding="utf-8") as file:
        file.write(formatted_xml + "\n")

    print(f"[SUCCESS] Generated sitemap: {sitemap_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <base_url>")
        sys.exit(1)

    base_url = sys.argv[1]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    rp = fetch_robots(f"{base_url.rstrip('/')}/robots.txt",
                      headers["User-Agent"])
    urls = extract_links(base_url, rp, headers)

    generate_sitemap(urls)


if __name__ == "__main__":
    main()
