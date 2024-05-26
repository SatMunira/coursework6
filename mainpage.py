import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

# Spotify API credentials
client_id = '13a4532e427c496592131815207589af'
client_secret = 'a07b3afe68fc403e8e70331c8483ac0d'


# Initialize Spotify API client
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Streamlit app title
st.title("Spotify Playlist Analyzer")


# Function to extract playlist ID from Spotify playlist link
def extract_playlist_id(link):
    start_index = link.find('playlist/') + len('playlist/')
    end_index = link.find('?')
    if start_index != -1 and end_index != -1:
        return link[start_index:end_index]
    else:
        return None


# Get the playlist link from user input
playlist_link = st.sidebar.text_input("Enter the link of the Spotify playlist:")

# Extract playlist ID from the link
playlist_id = extract_playlist_id(playlist_link) if playlist_link else None

# Add a dropdown menu for recommendation parameter
recommendation_parameter = st.sidebar.selectbox(
    "Recommend songs based on:",
    ["Default", "Decade", "Popularity"]
)


# Function to fetch playlist data
def fetch_playlist_data(playlist_id):
    playlist = sp.playlist(playlist_id)
    tracks = playlist["tracks"]["items"]
    track_ids = [track["track"]["id"] for track in tracks]
    track_names = [track["track"]["name"] for track in tracks]
    track_artists = [", ".join([artist["name"] for artist in track["track"]["artists"]]) for track in tracks]
    track_popularity = [track["track"]["popularity"] for track in tracks]
    track_duration = [track["track"]["duration_ms"] for track in tracks]
    track_album = [track["track"]["album"]["name"] for track in tracks]
    track_release_date = [track["track"]["album"]["release_date"] for track in tracks]
    track_cover_image = [track["track"]["album"]["images"] for track in tracks]
    artist_ids = [artist["id"] for track in tracks for artist in track["track"]["artists"]]
    return playlist, tracks, track_ids, track_names, track_artists, track_popularity, track_duration, track_album, track_release_date, track_cover_image, artist_ids


# Function to fetch artist genres
# Function to fetch artist genres
def fetch_artist_genres(artist_ids):
    genres = []
    for artist_id in artist_ids:
        try:
            artist_info = sp.artist(artist_id)
            artist_genres = artist_info.get("genres", [])
            genres.extend(artist_genres)
        except spotipy.SpotifyException as e:
            if e.http_status == 404:
                # Artist ID not found, skip it
                continue
            else:
                # Handle other exceptions if necessary
                raise
    return genres



# Function to extract decade from release date
def extract_decade(release_date):
    year = int(release_date.split("-")[0])
    decade = (year // 10) * 10
    return decade


# Function to get track recommendations based on selected parameter
def get_recommendations_by_parameter(track_ids, num_recommendations, parameter):
    if parameter == "Default":
        recommendations = sp.recommendations(seed_tracks=track_ids[:5], limit=num_recommendations)

    elif parameter == "Decade":
        decades = [extract_decade(track_release_date[i]) for i in range(len(track_release_date))]
        top_decade = Counter(decades).most_common(1)[0][0]
        recommendations = sp.recommendations(seed_tracks=track_ids[:5], limit=num_recommendations)
    elif parameter == "Popularity":
        top_popular_tracks = [track_id for _, track_id in sorted(zip(track_popularity, track_ids), reverse=True)[:5]]
        recommendations = sp.recommendations(seed_tracks=top_popular_tracks, limit=num_recommendations)

    rec_track_names = [track["name"] for track in recommendations["tracks"]]
    rec_track_artists = [", ".join([artist["name"] for artist in track["artists"]]) for track in
                         recommendations["tracks"]]
    rec_track_cover_image = [track["album"]["images"] for track in recommendations["tracks"]]
    return rec_track_names, rec_track_artists, rec_track_cover_image


if playlist_id:
    playlist, tracks, track_ids, track_names, track_artists, track_popularity, track_duration, track_album, track_release_date, track_cover_image, artist_ids = fetch_playlist_data(
        playlist_id)

    # Use columns to align image on the left and text on the right
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(playlist['images'][0]['url'], width=200)

    with col2:
        st.write(f"## {playlist['name']}")
        st.write(f"**Description:** {playlist['description']}")
        st.write(f"**Number of tracks:** {len(tracks)}")

    st.title('Playlist')


    # Function to display tracks
    def display_tracks(num_tracks_to_display):
        for i in range(num_tracks_to_display):
            col1, col2 = st.columns([1, 10])
            with col1:
                if len(track_cover_image[i]) > 0:
                    st.image(track_cover_image[i][0]['url'], width=50)
                else:
                    st.image(
                        'https://t3.ftcdn.net/jpg/04/60/01/36/360_F_460013622_6xF8uN6ubMvLx0tAJECBHfKPoNOR5cRa.jpg',
                        width=50)  # Provide a default image URL or placeholder
            with col2:
                st.markdown(f"**{track_names[i]}** by {track_artists[i]}")


    # Display initial set of tracks
    num_initial_tracks = 5
    display_tracks(num_initial_tracks)

    # Button to expand and show all tracks
    if len(track_names) > num_initial_tracks:
        if st.button('Show all tracks'):
            display_tracks(len(track_names))

    # Create a DataFrame from the playlist data
    data = {
        "Name": track_names,
        "Artist": track_artists,
        "Album": track_album,
        "Release Date": track_release_date,
        "Popularity": track_popularity,
        "Duration (ms)": track_duration
    }
    df = pd.DataFrame(data)

    # Display a histogram of track popularity
    fig_popularity = px.histogram(df, x="Popularity", nbins=20, title="Track Popularity Distribution")
    st.plotly_chart(fig_popularity)

    # Add a dropdown menu for bivariate analysis
    st.write("#### Bivariate Analysis")
    x_axis = st.selectbox("Select a variable for the x-axis:", ["Popularity", "Duration (ms)"])
    y_axis = st.selectbox("Select a variable for the y-axis:", ["Popularity", "Duration (ms)"])
    fig_bivariate = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs. {y_axis}")
    st.plotly_chart(fig_bivariate)

    # Extract decade for each track
    df["Decade"] = df["Release Date"].apply(extract_decade)

    # Count the number of tracks in each decade
    decade_counts = df["Decade"].value_counts().sort_index()

    # Calculate the total number of tracks
    total_tracks = decade_counts.sum()

    # Calculate the percentage of tracks in each decade
    decade_percentages = (decade_counts / total_tracks) * 100

    # Plot the circle diagram
    fig_circle = px.pie(
        names=decade_counts.index,
        values=decade_counts.values,
        title="Distribution of Songs by Decade",
        labels={"names": "Decade", "values": "Number of Songs"}
    )

    # Show the circle diagram
    st.plotly_chart(fig_circle)

    # Add a dropdown menu for multivariate analysis
    st.write("#### Multivariate Analysis")
    color_by = st.selectbox("Select a variable to color by:", ["Artist", "Album", "Release Date"])
    size_by = st.selectbox("Select a variable to size by:", ["Popularity", "Duration (ms)"])
    fig_multivariate = px.scatter(df, x="Duration (ms)", y="Popularity", color=color_by, size=size_by,
                                  hover_name="Name", title="Duration vs. Popularity Colored by Artist")
    st.plotly_chart(fig_multivariate)

    # Add a summary of the playlist data
    st.write("### Playlist Summary")
    st.write(
        f"**Most popular track:** {df.iloc[df['Popularity'].idxmax()]['Name']} by {df.iloc[df['Popularity'].idxmax()]['Artist']} ({df['Popularity'].max()} popularity)")
    st.write(
        f"**Least popular track:** {df.iloc[df['Popularity'].idxmin()]['Name']} by {df.iloc[df['Popularity'].idxmin()]['Artist']} ({df['Popularity'].min()} popularity)")

    # Display a bar chart of the top 10 most popular artists in the playlist
    st.write("#### Top 10 Artists")
    st.write("The bar chart below shows the top 10 most popular artists in the playlist.")
    top_artists = df.groupby("Artist")["Popularity"].mean().sort_values(ascending=False).head(10)
    fig_top_artists = px.bar(top_artists, x=top_artists.index, y=top_artists.values,
                             title="Top 10 Artists by Average Popularity",
                             labels={"x": "Artist", "y": "Average Popularity"})
    st.plotly_chart(fig_top_artists)


    # Function to display top ten tracks based on popularity
    def display_top_tracks():
        top_tracks_indices = df["Popularity"].argsort()[::-1][:10]  # Get indices of top ten tracks based on popularity
        for i in top_tracks_indices:
            col1, col2 = st.columns([1, 10])
            with col1:
                if len(track_cover_image[i]) > 0:
                    st.image(track_cover_image[i][0]['url'], width=50)
                else:
                    st.image(
                        'https://t3.ftcdn.net/jpg/04/60/01/36/360_F_460013622_6xF8uN6ubMvLx0tAJECBHfKPoNOR5cRa.jpg',
                        width=50)  # Provide a default image URL or placeholder
            with col2:
                st.markdown(f"**{track_names[i]}** by {track_artists[i]}")


    # Display top ten tracks based on popularity
    st.title("Top 10 Tracks")
    display_top_tracks()

    # Get the number of recommendations to display
    num_recommendations = st.slider("Number of recommendations:", min_value=1, max_value=20, value=5)

    if st.button('Get Recommendations'):
        rec_track_names, rec_track_artists, rec_track_cover_image = get_recommendations_by_parameter(track_ids,
                                                                                                     num_recommendations,
                                                                                                     recommendation_parameter)

        for i in range(len(rec_track_names)):
            col1, col2 = st.columns([1, 10])
            with col1:
                if len(rec_track_cover_image[i]) > 0:
                    st.image(rec_track_cover_image[i][0]['url'], width=50)
                else:
                    st.image(
                        'https://t3.ftcdn.net/jpg/04/60/01/36/360_F_460013622_6xF8uN6ubMvLx0tAJECBHfKPoNOR5cRa.jpg',
                        width=50)  # Provide a default image URL or placeholder
            with col2:
                st.markdown(f"**{rec_track_names[i]}** by {rec_track_artists[i]}")


    # Function to create a new playlist with recommended tracks
    def create_playlist_with_recommendations(user_id, playlist_name, track_uris):
        # Create a new playlist
        new_playlist = sp.user_playlist_create(user_id, playlist_name)

        # Add recommended tracks to the new playlist
        sp.playlist_add_items(new_playlist['id'], track_uris)

        return new_playlist


    # Get user ID
    user_id = sp.me()['id']


    # Function to get track URIs from track names and artists
    def get_track_uris(track_names, track_artists):
        track_uris = []
        for i in range(len(track_names)):
            track_name = track_names[i]
            track_artist = track_artists[i]
            result = sp.search(q=f"track:{track_name} artist:{track_artist}", type='track')
            if result['tracks']['items']:
                track_uri = result['tracks']['items'][0]['uri']
                track_uris.append(track_uri)
        return track_uris


    # Get track URIs for recommended tracks
    track_uris = get_track_uris(rec_track_names, rec_track_artists)

    # Create a new playlist with recommended tracks
    new_playlist = create_playlist_with_recommendations(user_id, "Recommended Playlist", track_uris)

    # Display the link to the new playlist
    st.write("### New Playlist Created")
    st.write(f"**Playlist Name:** {new_playlist['name']}")
    st.write(f"**Playlist Link:** [Open Playlist]({new_playlist['external_urls']['spotify']})")

else:
    st.write("Please enter a valid Spotify playlist link.")
