import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/117.0 Safari/537.36"
}


def fetch_website_contents(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    for irrelevant in soup.body(["script", "style", "img", "input"]):
        irrelevant.decompose()
    text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
    return f"Webpage Title:\n{title}\nWebpage Contents:\n{text}\n\n"


def fetch_website_links(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [a.get("href") for a in soup.find_all("a")]
    return [link for link in links if link]
