import requests


HEADERS = {
    "User-Agent": "QAResearchPipeline/1.0 (research project; contact: begum.atay0106@gmail.com)"
}


def fetch_article_from_url(url: str):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    article_title = url.rsplit("/", 1)[-1]

    api_url = "https://tr.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "redirects": 1,
        "titles": article_title,
    }

    api_response = requests.get(
        api_url,
        params=params,
        headers=HEADERS,
        timeout=30,
    )

    api_response.raise_for_status()

    data = api_response.json()

    page = next(iter(data["query"]["pages"].values()))

    return {
        "title": page["title"],
        "url": url,
        "text": page.get("extract", ""),
    }