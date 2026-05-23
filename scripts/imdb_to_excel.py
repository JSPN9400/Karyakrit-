"""
Fetch IMDb Top 250 movies using IMDbPY and save to Excel.

Usage:
    python scripts/imdb_to_excel.py

Output:
    data/imdb_top250.xlsx

Notes:
- Requires `IMDbPY` and `pandas` (pandas already in project). Install with:
    pip install IMDbPY
"""

from imdb import IMDb
import pandas as pd
import os


def fetch_top250(limit=None):
    ia = IMDb()
    top250 = ia.get_top250_movies()
    if limit:
        top250 = top250[:limit]
    movies = []
    for m in top250:
        ia.update(m)
        title = m.get('title')
        year = m.get('year')
        rating = m.get('rating')
        url = f"https://www.imdb.com/title/{m.movieID}/"
        genres = ', '.join(m.get('genres', []))
        directors = ', '.join([d['name'] for d in m.get('directors', [])]) if m.get('directors') else ''
        cast = ', '.join([p['name'] for p in m.get('cast', [])[:5]]) if m.get('cast') else ''
        movies.append({
            'title': title,
            'year': year,
            'rating': rating,
            'genres': genres,
            'directors': directors,
            'top_cast': cast,
            'url': url
        })
    return movies


def save_to_excel(movies, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(movies)
    df.to_excel(path, index=False)
    return path


def main():
    print("Fetching IMDb Top 250 (this may take a minute)...")
    movies = fetch_top250()
    out = save_to_excel(movies, os.path.join('data', 'imdb_top250.xlsx'))
    print(f"Saved {len(movies)} movies to {out}")
    if movies:
        top = movies[0]
        print(f"Top movie: {top['title']} ({top['year']}) — rating {top['rating']}")

if __name__ == '__main__':
    main()
