import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import json
from typing import Dict, Optional
import uuid
from model_wrapper import ModelWrapper
from logger import get_module_logger, get_request_logger

# Initialize module logger
logger = get_module_logger(__name__)

# Initialize the model wrapper
model_wrapper = None

def init_model_wrapper() -> None:
    """Initialize the model wrapper using API key from secrets.toml."""
    global model_wrapper
    try:
        model_wrapper = ModelWrapper()
        st.session_state['model_wrapper'] = model_wrapper
        logger.info("Model wrapper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model wrapper: {str(e)}")
        st.error("Failed to initialize Gemini API. Please check your secrets.toml file.")

def setup_selenium():
    """Configure and return a Selenium WebDriver instance."""
    options = Options()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")
    return webdriver.Chrome(options=options)

def scroll_page(driver):
    """Scroll the page to load dynamic content."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def clean_html(html_content: str, clean_attributes: bool = True) -> str:
    """
    Clean HTML content by removing unwanted tags and optionally cleaning attributes.

    Args:
        html_content (str): Raw HTML content to clean
        clean_attributes (bool): Whether to clean attributes from tags

    Returns:
        str: Cleaned HTML content
    """
    unwanted_tags = [
        "script", "style", "meta", "footer", "header",
        "nav", "aside", "form", "iframe", "noscript"
    ]

    soup = BeautifulSoup(html_content, "html.parser")

    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()

    if clean_attributes:
        for element in soup.find_all(True):
            if element.name not in ["a", "img"]:
                if element.name == "a":
                    href = element.get("href")
                    element.attrs = {"href": href} if href else {}
                elif element.name == "img":
                    src = element.get("src")
                    alt = element.get("alt")
                    element.attrs = {k: v for k, v in {"src": src, "alt": alt}.items() if v}
                else:
                    element.attrs = {}

    cleaned_html = str(soup)
    cleaned_html = "\n".join(
        line.strip() for line in cleaned_html.splitlines() if line.strip()
    )

    return cleaned_html

def extract_links(soup, base_url):
    """Extract all links from the page."""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('http'):
            links.append(href)
        elif href.startswith('/'):
            links.append(base_url.rstrip('/') + href)
    return list(set(links))

def scrape_url(url, extract_links_flag=False, max_links=5):
    """Main function to scrape content from a URL."""
    try:
        driver = setup_selenium()
        driver.get(url)

        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        scroll_page(driver)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        main_content = clean_html(page_source, clean_attributes=True)

        links_data = []
        if extract_links_flag:
            all_links = extract_links(soup, url)
            for link in all_links[:max_links]:
                try:
                    driver.get(link)
                    time.sleep(2)
                    link_content = clean_html(driver.page_source)
                    links_data.append({
                        'url': link,
                        'content': link_content[:500] + '...' if len(link_content) > 500 else link_content
                    })
                except Exception as e:
                    st.error(f"Error scraping link {link}: {str(e)}")

        driver.quit()
        return main_content, links_data

    except Exception as e:
        st.error(f"Error during scraping: {str(e)}")
        return None, []
    finally:
        if 'driver' in locals():
            driver.quit()

def main():
    st.title("🕷️ Web Scraper with Gemini Analysis")
    st.write("Enter a URL to scrape its content using Selenium and BeautifulSoup, then analyze with Gemini")

    url = st.text_input("Enter URL:", "")

    col1, col2 = st.columns(2)
    with col1:
        extract_links_flag = st.checkbox("Extract links from page", value=False)
    with col2:
        max_links = st.number_input("Maximum links to scrape", min_value=1, max_value=10, value=5)

    if st.button("Start Scraping"):
        if url:
            with st.spinner("Scraping in progress..."):
                # Initialize data dictionary
                full_data = {
                    'url': url,
                    'main_content': None,
                    'linked_pages': [],
                    'gemini_analysis': None
                }

                progress_bar = st.progress(0)

                main_content, links_data = scrape_url(url, extract_links_flag, max_links)

                if main_content:
                    progress_bar.progress(50)

                    full_data['main_content'] = main_content
                    full_data['linked_pages'] = links_data

                    st.subheader("Main Content")
                    st.text_area("Extracted Content", main_content[:1000] + "..."
                               if len(main_content) > 1000 else main_content,
                               height=200)

                    if 'model_wrapper' not in st.session_state:
                        init_model_wrapper()

                    if 'model_wrapper' in st.session_state:
                        st.subheader("Gemini Analysis")
                        with st.spinner("Analyzing content with Gemini..."):
                            # Option 2: Treat analysis as plain text
                            analysis = st.session_state['model_wrapper'].analyze_html_content(
                                html_content=main_content
                            )
                            st.markdown(analysis)
                            full_data['gemini_analysis'] = analysis

                    if links_data:
                        st.subheader("Extracted Links Content")
                        for idx, link_data in enumerate(links_data, 1):
                            with st.expander(f"Link {idx}: {link_data['url']}", expanded=False):
                                st.write(link_data['content'])

                    st.download_button(
                        label="Download as JSON",
                        data=json.dumps(full_data, indent=2),
                        file_name="scraped_data.json",
                        mime="application/json"
                    )

                    if links_data:
                        df = pd.DataFrame(links_data)
                        st.download_button(
                            label="Download Links as CSV",
                            data=df.to_csv(index=False).encode('utf-8'),
                            file_name="scraped_links.csv",
                            mime="text/csv"
                        )

                    progress_bar.progress(100)
                    st.success("Scraping completed successfully!")
        else:
            st.warning("Please enter a URL to scrape")

if __name__ == "__main__":
    main()
