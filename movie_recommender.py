import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
from difflib import get_close_matches
import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MOVIES_CSV = 'movies.csv'
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_films_voted_the_best"

def scrape_wikipedia_best_movies(output_csv=MOVIES_CSV):
    """Scrape Wikipedia's 'List of films voted the best' page with proper genre detection"""
    try:
        logger.info(f"Scraping {WIKI_URL}")
        resp = requests.get(WIKI_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        movies = []
        current_genre = "General"
        
        # Find all headings (h2, h3, h4) and process sequentially
        all_elements = soup.find_all(['h2', 'h3', 'h4', 'ul'])
        
        # Known genre keywords to look for
        genre_keywords = {
            'action': 'Action',
            'animation': 'Animation', 
            'christmas': 'Christmas',
            'comedy': 'Comedy',
            'disaster': 'Disaster',
            'documentary': 'Documentary',
            'fantasy': 'Fantasy',
            'horror': 'Horror',
            'lgbt': 'LGBT',
            'musical': 'Musical',
            'romance': 'Romance',
            'science fiction': 'Science Fiction',
            'sci-fi': 'Science Fiction',
            'silent': 'Silent',
            'sports': 'Sports',
            'superhero': 'Superhero',
            'war': 'War',
            'western': 'Western'
        }
        
        logger.info("Processing elements sequentially to match movies with genres...")
        
        for element in all_elements:
            if element.name in ['h2', 'h3', 'h4']:
                heading_text = element.get_text().strip().lower()
                clean_heading = re.sub(r'\[.*?\]', '', heading_text).strip()
                clean_heading = re.sub(r'\s*\(edit\)\s*', '', clean_heading).strip()
                
                # Check if this heading matches any genre keyword
                for keyword, genre_name in genre_keywords.items():
                    if keyword in clean_heading:
                        current_genre = genre_name
                        logger.info(f"Found genre section: '{clean_heading}' -> {genre_name}")
                        break
                        
            elif element.name == 'ul' and current_genre != "General":
                # Extract movies from this list under the current genre
                movie_count = 0
                for li in element.find_all('li'):
                    movie_data = extract_movie_from_li(li, current_genre)
                    if movie_data:
                        movies.append(movie_data)
                        movie_count += 1
                
                if movie_count > 0:
                    logger.info(f"Found {movie_count} movies in {current_genre}")
        
        # If no genre-specific movies found, fall back to general scraping
        if not movies:
            logger.info("No genre-specific movies found, using general approach...")
            return scrape_general_movies(soup, output_csv)
        
        # Create DataFrame and save
        df = pd.DataFrame(movies, columns=['Title', 'Genre', 'Rating', 'Year'])
        df = df.drop_duplicates(subset=['Title', 'Year'])
        df = df[df['Title'].str.len() > 0]
        
        df.to_csv(output_csv, index=False)
        logger.info(f"Successfully scraped {len(df)} movies across {len(df['Genre'].unique())} genres")
        print(f"Successfully scraped {len(df)} movies from Wikipedia!")
        print(f"Found genres: {', '.join(sorted(df['Genre'].unique()))}")
        return df

    except Exception as e:
        logger.error(f"Scraping error: {e}")
        print(f"Scraping error: {e}")
        return None

def scrape_general_movies(soup, output_csv):
    """Fallback scraping for general movie data"""
    try:
        movies = []
        
        # Look for movie patterns in all list items
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                text = li.get_text(" ", strip=True)
                
                # Look for movie title patterns
                patterns = [
                    r'^(.*?)\s+\((\d{4})\)',  # Title (Year)
                    r'^(.*?)\s*-\s*(\d{4})',  # Title - Year
                    r'^(.*?),\s*(\d{4})',     # Title, Year
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        title = match.group(1).strip()
                        year = match.group(2)
                        
                        # Skip very short titles or obvious non-movies
                        if len(title) < 3 or any(word in title.lower() for word in ['list', 'category', 'section', 'see also']):
                            continue
                            
                        movies.append([title, "General", "N/A", year])
                        break
        
        if movies:
            df = pd.DataFrame(movies, columns=['Title', 'Genre', 'Rating', 'Year'])
            df = df.drop_duplicates(subset=['Title', 'Year'])
            df.to_csv(output_csv, index=False)
            logger.info(f"General scraping saved {len(df)} movies")
            print(f"Found {len(df)} movies with general scraping!")
            return df
        else:
            logger.error("No movies found")
            print("No movies found during scraping.")
            return None
            
    except Exception as e:
        logger.error(f"General scraping error: {e}")
        return None

def extract_movie_from_li(li, genre):
    """Extract movie information from a list item"""
    try:
        text = li.get_text(" ", strip=True)
        
        # Primary pattern: Title (Year)
        match = re.match(r"^(.*?)\s+\((\d{4})\)", text)
        if match:
            title = match.group(1).strip()
            year = match.group(2)
            return [title, genre, "N/A", year]
        
        # Secondary pattern: Title mentioned in sentences
        sentence_match = re.match(r"^([^.!?]+?)(?:\s+was|\s+is|\s+has been|\s+won|\s+received)", text)
        if sentence_match:
            title = sentence_match.group(1).strip()
            title = re.sub(r'\s*\([^)]*\)\s*', ' ', title).strip()
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            year = year_match.group(0) if year_match else ""
            
            if len(title) > 2:
                return [title, genre, "N/A", year]
        
        return None
        
    except Exception as e:
        return None

def load_and_clean_movies(csv_file=MOVIES_CSV):
    """Load and clean movie data from CSV"""
    try:
        if not os.path.exists(csv_file):
            return None
            
        df = pd.read_csv(csv_file)
        if df.empty:
            return None
        
        # Clean the data
        df.dropna(subset=['Title', 'Genre'], inplace=True)
        df['Genre'] = df['Genre'].str.lower().str.replace(' ', '')
        df.drop_duplicates(subset=['Title', 'Year'], inplace=True)
        
        return df
        
    except Exception as e:
        print(f"Error loading movies: {e}")
        return None

def filter_movies_by_genres(df, genres):
    """Filter movies by selected genres"""
    genres = [g.strip().lower().replace(' ', '') for g in genres]
    mask = df['Genre'].apply(lambda g: any(gen in str(g).lower() for gen in genres))
    return df[mask]

def get_all_genres(df):
    """Get all unique genres from the dataset"""
    genres = set()
    for g in df['Genre'].dropna():
        genre_parts = str(g).split(',')
        for part in genre_parts:
            clean_genre = part.strip().lower()
            if clean_genre and clean_genre not in ["unknown", "n/a"]:
                genres.add(clean_genre)
    return list(genres)

def get_genre_suggestions(chosen_genres, all_genres, cutoff=0.6):
    """Get suggestions for similar genres when no matches found"""
    suggestions = {}
    for genre in chosen_genres:
        matches = get_close_matches(genre.lower(), all_genres, n=3, cutoff=cutoff)
        if matches:
            suggestions[genre] = matches
    return suggestions

def recommend_movies(df, chosen_genres, num_recommendations=5):
    """Get movie recommendations based on chosen genres"""
    filtered = filter_movies_by_genres(df, chosen_genres)
    
    if filtered.empty:
        all_genres = get_all_genres(df)
        suggestions = get_genre_suggestions(chosen_genres, all_genres)
        
        print("\nNo movies found for your genre(s).")
        if suggestions:
            print("Did you mean:")
            for genre, matches in suggestions.items():
                print(f"  '{genre}': {', '.join(matches)}")
        print("Try again with different genres!")
        return
    
    print(f"\nGreat! Found {len(filtered)} movies matching your preferences.")
    print(f"Here are {min(num_recommendations, len(filtered))} random recommendations:\n")
    
    # Sample random movies
    sample_size = min(num_recommendations, len(filtered))
    recommendations = filtered.sample(sample_size)
    
    # Display recommendations
    for i, (_, movie) in enumerate(recommendations.iterrows(), 1):
        print(f"{i}. {movie['Title']}")
        print(f"   Genre: {movie['Genre']}")
        if pd.notna(movie['Year']) and movie['Year']:
            print(f"   Year: {movie['Year']}")
        if pd.notna(movie['Rating']) and movie['Rating'] != 'N/A':
            print(f"   Rating: {movie['Rating']}")
        print()

def main():
    """Main CLI interface"""
    print("=" * 60)
    print("🎬 MOVIE RECOMMENDATION ENGINE 🎬")
    print("=" * 60)
    print("Welcome! This tool helps you discover great movies based on your favorite genres.")
    print("Data is sourced from Wikipedia's 'List of films voted the best'.\n")
    
    # Data setup
    print("📥 DATA SETUP")
    print("-" * 20)
    
    if os.path.exists(MOVIES_CSV):
        try:
            df_check = pd.read_csv(MOVIES_CSV)
            if not df_check.empty:
                print(f"✓ Found existing data: {len(df_check)} movies")
                print("Using existing data. Delete 'movies.csv' to scrape fresh data.\n")
            else:
                print("📥 Existing CSV file is empty, scraping fresh data...")
                result = scrape_wikipedia_best_movies()
                if result is None:
                    print("❌ Scraping failed. Exiting.")
                    return
        except:
            print("📥 Error reading existing data, scraping fresh data...")
            result = scrape_wikipedia_best_movies()
            if result is None:
                print("❌ Scraping failed. Exiting.")
                return
    else:
        print("📥 No existing data found, scraping Wikipedia...")
        result = scrape_wikipedia_best_movies()
        if result is None:
            print("❌ Scraping failed. Exiting.")
            return
    
    # Load data
    print("\n📊 LOADING DATA")
    print("-" * 20)
    df = load_and_clean_movies()
    if df is None or df.empty:
        print("❌ No movies available for recommendations.")
        return
    
    print(f"✓ Loaded {len(df)} movies successfully!")
    
    # Show available genres
    genres = sorted(get_all_genres(df))
    if genres:
        print(f"\n🏷️  AVAILABLE GENRES ({len(genres)} total)")
        print("-" * 30)
        for i, genre in enumerate(genres):
            print(f"{genre.ljust(20)}", end="")
            if (i + 1) % 3 == 0:
                print()
        if len(genres) % 3 != 0:
            print()
    else:
        print("\n⚠️  No specific genres detected. You can try searching for 'general'.")
    
    # Recommendation loop
    print(f"\n🎯 MOVIE RECOMMENDATIONS")
    print("-" * 30)
    print("Enter your preferred genres (comma-separated) to get personalized recommendations!")
    print("Examples: 'action', 'comedy, horror', 'western, war'\n")
    
    while True:
        try:
            user_input = input("🎬 Enter genre(s) (or 'quit' to exit): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n🎭 Thanks for using the Movie Recommendation Engine!")
                print("Hope you discover some amazing films! Goodbye! 🍿")
                break
            
            if not user_input:
                print("Please enter at least one genre.")
                continue
            
            chosen_genres = [g.strip() for g in user_input.split(',') if g.strip()]
            if not chosen_genres:
                print("Please enter valid genres.")
                continue
            
            print(f"\n🔍 Searching for movies in: {', '.join(chosen_genres)}")
            recommend_movies(df, chosen_genres)
            
            print("-" * 50)
            
        except (KeyboardInterrupt, EOFError):
            print("\n\n🎭 Thanks for using the Movie Recommendation Engine! Goodbye! 🍿")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again with different input.")

if __name__ == "__main__":
    main()
