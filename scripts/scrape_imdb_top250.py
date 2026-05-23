"""
Scrape IMDb Top 250 page and save to Excel (data/imdb_top250.xlsx).

This uses requests + BeautifulSoup and is intended for personal use.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

URL = 'https://www.imdb.com/chart/top/'


def scrape_top250():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36'}
    r = requests.get(URL, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    table = soup.find('tbody', class_='lister-list')
    movies = []
    for row in table.find_all('tr'):
        title_column = row.find('td', class_='titleColumn')
        rating_column = row.find('td', class_='ratingColumn imdbRating')
        if not title_column:
            continue
        anchor = title_column.find('a')
        title = anchor.text.strip()
        href = anchor['href']
        url = f"https://www.imdb.com{href.split('?')[0]}"
        year = title_column.find('span', class_='secondaryInfo').text.strip('()')
        rating = rating_column.find('strong').text.strip() if rating_column and rating_column.find('strong') else ''
        movies.append({'title': title, 'year': int(year) if year.isdigit() else year, 'rating': float(rating) if rating else None, 'url': url})

    return movies


def save(movies, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(movies)
    df.to_excel(path, index=False)
    return path


def main():
    print('Scraping IMDB Top 250...')
    movies = scrape_top250()
    out = save(movies, os.path.join('data', 'imdb_top250.xlsx'))
    print(f'Saved {len(movies)} movies to {out}')
    if movies:
        top = movies[0]
        print(f"Top movie: {top['title']} ({top['year']}) — rating {top['rating']}")

if __name__ == '__main__':
    main()
