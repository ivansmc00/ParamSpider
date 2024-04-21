import argparse
import os
import logging
from . import client  # Importing client from a module named "client"
from urllib.parse import urlparse, parse_qs, urlencode
import colorama
from colorama import Fore, Style

yellow_color_code = "\033[93m"
reset_color_code = "\033[0m"

colorama.init(autoreset=True)  # Initialize colorama for colored terminal output

log_format = '%(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
logging.getLogger('').handlers[0].setFormatter(logging.Formatter(log_format))

HARDCODED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".svg", ".json",
    ".css", ".js", ".webp", ".woff", ".woff2", ".eot", ".ttf", ".otf", ".mp4", ".txt"
]

def has_extension(url, extensions):
    parsed_url = urlparse(url)
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    return extension in extensions

def clean_url(url):
    parsed_url = urlparse(url)
    if (parsed_url.port == 80 and parsed_url.scheme == "http") or (parsed_url.port == 443 and parsed_url.scheme == "https"):
        parsed_url = parsed_url._replace(netloc=parsed_url.netloc.rsplit(":", 1)[0])
    return parsed_url.geturl()

def clean_urls(urls, extensions, placeholder):
    cleaned_urls = set()
    for url in urls:
        cleaned_url = clean_url(url)
        if not has_extension(cleaned_url, extensions):
            parsed_url = urlparse(cleaned_url)
            query_params = parse_qs(parsed_url.query)
            cleaned_query = "&".join(f"{k}={','.join(v)}" if len(v) > 1 else f"{k}={v[0]}" for k, v in query_params.items())
            cleaned_url = parsed_url._replace(query=cleaned_query).geturl()
            cleaned_urls.add(cleaned_url)
    return list(cleaned_urls)

def fetch_and_clean_urls(domain, extensions, stream_output, proxy, placeholder):
    wayback_uri = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=txt&collapse=urlkey&fl=original&page=/"
    response = client.fetch_url_content(wayback_uri, proxy)
    urls = response.text.split()
    cleaned_urls = clean_urls(urls, extensions, placeholder)

    for url in cleaned_urls:
        if "?" in url:
            print(url)

def main():
    parser = argparse.ArgumentParser(description="Mining URLs from dark corners of Web Archives")
    parser.add_argument("-d", "--domain", help="Domain name to fetch related URLs for.")
    parser.add_argument("-l", "--list", help="File containing a list of domain names.")
    parser.add_argument("-s", "--stream", action="store_true", help="Stream URLs on the terminal.")
    parser.add_argument("--proxy", help="Set the proxy address for web requests.", default=None)
    parser.add_argument("-p", "--placeholder", help="Placeholder for parameter values", default="FUZZ")
    args = parser.parse_args()

    if not args.domain and not args.list:
        parser.error("Please provide either the -d option or the -l option.")

    if args.domain and args.list:
        parser.error("Please provide either the -d option or the -l option, not both.")

    if args.list:
        with open(args.list, "r") as f:
            domains = [line.strip().lower().replace('https://', '').replace('http://', '') for line in f.readlines()]
            domains = [domain for domain in domains if domain]
            domains = list(set(domains))
        for domain in domains:
            fetch_and_clean_urls(domain, HARDCODED_EXTENSIONS, args.stream, args.proxy, args.placeholder)
    else:
        domain = args.domain
        fetch_and_clean_urls(domain, HARDCODED_EXTENSIONS, args.stream, args.proxy, args.placeholder)

if __name__ == "__main__":
    main()

