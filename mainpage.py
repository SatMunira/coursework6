import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px

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
    return playlist, tracks, track_ids, track_names, track_artists, track_popularity, track_duration, track_album, track_release_date, track_cover_image



# Function to get track recommendations
def get_recommendations(track_ids, num_recommendations):
    recommendations = sp.recommendations(seed_tracks=track_ids[:5], limit=num_recommendations)
    rec_track_names = [track["name"] for track in recommendations["tracks"]]
    rec_track_artists = [", ".join([artist["name"] for artist in track["artists"]]) for track in
                         recommendations["tracks"]]
    rec_track_cover_image = [track["album"]["images"] for track in recommendations["tracks"]]
    return rec_track_names, rec_track_artists, rec_track_cover_image


if playlist_id:
    playlist, tracks, track_ids, track_names, track_artists, track_popularity, track_duration, track_album, track_release_date, track_cover_image = fetch_playlist_data(
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
    fig_top_artists = px.bar(x=top_artists.index, y=top_artists.values, title="Top 10 Artists")
    st.plotly_chart(fig_top_artists)

    # Display a bar chart of the top 10 most popular songs in the playlist
    st.write("#### Top 10 Songs")
    st.write("The bar chart below shows the top 10 most popular songs in the playlist.")
    top_songs = df.groupby("Name")["Popularity"].mean().sort_values(ascending=False).head(10)
    fig_top_songs = px.bar(x=top_songs.index, y=top_songs.values, title="Top 10 Songs")
    st.plotly_chart(fig_top_songs)

    # Get and display recommendations
    st.write("### Recommended Tracks")

    num_recommendations = st.radio(
        "Select the number of recommended songs:",
        (20, 30, 50)
    )

    if st.button('Get Recommendations'):
        rec_track_names, rec_track_artists, rec_track_cover_image = get_recommendations(track_ids, num_recommendations)

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
else:
    st.write("Please enter a valid Spotify playlist link.")
