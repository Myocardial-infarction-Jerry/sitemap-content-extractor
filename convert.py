import os
from bs4 import BeautifulSoup


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


if __name__ == "__main__":
    convert_html_to_markdown()
