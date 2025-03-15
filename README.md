# Sitemap Content Extractor

This project is a simple tool to extract content from a sitemap. It fetches the sitemap XML file from a given URL, retrieves the URLs listed in it, and saves the content of those URLs as HTML files. Additionally, it can convert the saved HTML files to Markdown format.

## Features

- Fetch sitemap XML files from a URL
- Extract URLs from the sitemap
- Save the content of the URLs as HTML files
- Convert saved HTML files to Markdown format
- Simple and easy to use

## How to Use

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/sitemap-content-extractor.git
    cd sitemap-content-extractor
    ```

2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Run the extractor:
    ```sh
    python main.py <base_url>
    ```

    Replace `<base_url>` with the base URL of the website. The script will automatically append `/sitemap.xml` and `/robots.txt` to this base URL.

4. The extracted URLs will be printed to the console, and the content will be saved in the `articles` directory.

5. To convert the saved HTML files to Markdown format, the script will automatically run the conversion after fetching the articles.

## Example

```sh
python main.py https://example.com
```

This will output the URLs listed in `https://example.com/sitemap.xml`, save the content of those URLs as HTML files in the `articles` directory, and convert them to Markdown format.

## Using sitemap.py

1. Run the `sitemap.py` script:
    ```sh
    python sitemap.py <base_url>
    ```

    Replace `<base_url>` with the base URL of the website. This script will fetch the sitemap, extract the URLs, and save them to a file named `sitemap_urls.txt` in the project directory.

2. The extracted URLs will be saved in `sitemap_urls.txt` for further processing or analysis.

## Using match.py

1. Install the `ollama` package:
    ```sh
    pip install ollama
    ```

2. Pull the required model for embedding:
    ```sh
    ollama pull nomic-embed-text
    ```

3. Run the `match.py` script:
    ```sh
    python match.py
    ```

    This script will read all `.md` files from the `texts/` directory, embed their content along with the specified keywords, and sort the files based on their relevance to the keywords.

4. The sorted files along with their relevance scores will be printed to the console.


