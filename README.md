Movie Recommender

A Python-based web scraping and movie recommendation system that collects data from Wikipedia's "List of films voted the best" page.

 Description
This project scrapes movie information from Wikipedia and creates a movie recommendation system. It uses BeautifulSoup for web scraping and includes genre detection capabilities.

 Features
- Web scrapes movie data from Wikipedia
- Automatically categorizes movies by genre
- Includes logging functionality for debugging
- Handles various genre classifications including:
  - Action
  - Animation
  - Christmas
  - Comedy
  - Disaster
  - Documentary
  - Fantasy
  - Horror
  - LGBT
  - Musical
  - Romance
  - Science Fiction
  - Silent
  - Sports
  - Superhero
  - War
  - Western

 Dependencies
- requests
- BeautifulSoup4
- pandas
- logging

 Usage
The script uses Wikipedia's "List of films voted the best" page as its data source and saves the scraped data to a CSV file named 'movies.csv'.

 Technical Details
- URL: https://en.wikipedia.org/wiki/List_of_films_voted_the_best
- Output: movies.csv
- Logging: Includes detailed logging for debugging and monitoring

 Error Handling
The script includes error handling for web requests and data processing with proper logging mechanisms.
