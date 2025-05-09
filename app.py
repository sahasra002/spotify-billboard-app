from flask import Flask, request
from bs4 import BeautifulSoup
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
import time
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Ensure required environment variables are set
if not os.getenv("SPOTIFY_CLIENT_ID") or not os.getenv("SPOTIFY_CLIENT_SECRET") or not os.getenv("SPOTIFY_REDIRECT_URI"):
    raise EnvironmentError("Missing Spotify API credentials in the .env file.")

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    form_html = '''
        <h2>Create Billboard Top 100 Spotify Playlist</h2>
        <form method="POST">
            <label>Enter a date (YYYY-MM-DD): </label>
            <input type="text" name="date" required>
            <button type="submit">Generate Playlist</button>
        </form>
    '''

    if request.method == "POST":
        travel_date = request.form["date"]

        try:
            # Validate date
            if datetime.strptime(travel_date, "%Y-%m-%d") > datetime.today():
                return form_html + "<p style='color:red;'>❌ Billboard Hot 100 is not available for future dates!</p>"

            # Billboard scraping
            URL = f"https://www.billboard.com/charts/hot-100/{travel_date}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(URL, headers=headers)
            response.raise_for_status()  # Ensure the request was successful
            soup = BeautifulSoup(response.text, "html.parser")
            song_tags = soup.select("li ul li h3")
            songs = [tag.get_text(strip=True) for tag in song_tags]

            if not songs:
                return form_html + "<p style='color:red;'>⚠️ No songs found for the given date. Please try another date.</p>"

            # Spotify Auth
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
                scope="playlist-modify-private"
            ))

            user_id = sp.current_user()["id"]
            playlist = sp.user_playlist_create(
                user=user_id,
                name=f"{travel_date} Billboard 100",
                public=False,
                description=f"Top 100 songs from Billboard on {travel_date}"
            )

            year = travel_date.split("-")[0]
            song_uris = []

            for song in songs:
                try:
                    result = sp.search(q=f"track:{song} year:{year}", type="track", limit=1)
                    if result["tracks"]["items"]:
                        uri = result["tracks"]["items"][0]["uri"]
                        song_uris.append(uri)
                    time.sleep(0.2)  # Rate limiting
                except Exception as e:
                    logging.error(f"Error searching for song '{song}': {e}")

            sp.playlist_add_items(playlist_id=playlist["id"], items=song_uris)
            playlist_url = playlist["external_urls"]["spotify"]

            logging.debug(f"Spotify playlist URL: {playlist_url}")

            song_preview = "<ol>" + "".join([f"<li>{s}</li>" for s in songs[:10]]) + "</ol>"
            return form_html + f"<p>✅ Playlist Created: <a href='{playlist_url}' target='_blank'>View on Spotify</a></p>" + "<h4>Top 10 Songs:</h4>" + song_preview

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Billboard data: {e}")
            return form_html + f"<p style='color:red;'>⚠️ Error fetching Billboard data: {e}</p>"
        except spotipy.exceptions.SpotifyException as e:
            error_message = str(e)
            if "Invalid client" in error_message:
                return form_html + "<p style='color:red;'>⚠️ Invalid Spotify credentials. Please check your .env file.</p>"
            return form_html + f"<p style='color:red;'>⚠️ Spotify API Error: {error_message}</p>"
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return form_html + f"<p style='color:red;'>⚠️ An unexpected error occurred: {e}</p>"

    return form_html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

