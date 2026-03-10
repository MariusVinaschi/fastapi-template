import requests
from prefect import flow, task


@task(retries=3, retry_delay_seconds=2)
def fetch_html(url: str) -> str:
    """Download page HTML (with retries).

    This is just a regular requests call - Prefect adds retry logic
    without changing how we write the code."""
    print(f"Fetching {url} …")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


@flow(name="Simple web scrapper", log_prints=True)
async def scrape(urls: str) -> str:
    html = fetch_html(urls)
    return html
