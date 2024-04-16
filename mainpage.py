import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st
import pandas as pd
import plotly.express as px

client_id = '13a4532e427c496592131815207589af'
client_secret = 'a07b3afe68fc403e8e70331c8483ac0d'

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

st.title("Spotify Playlist Analyzer")
# Function to extract playlist ID from Spotify playlist link
def extract_playlist_id(link):
    # Find the index of 'playlist/' and '?'
    start_index = link.find('playlist/') + len('playlist/')
    end_index = link.find('?')
    if start_index != -1 and end_index != -1:
        # Extract the substring between 'playlist/' and '?'
        playlist_id = link[start_index:end_index]
        return playlist_id
    else:
        return None

# Get the playlist link from user input
playlist_link = st.sidebar.text_input("Enter the link of the Spotify playlist:")

# Extract playlist ID from the link
playlist_id = None
if playlist_link:
    playlist_id = extract_playlist_id(playlist_link)

if playlist_id:
    # Use the playlist ID to fetch the playlist
    playlist = sp.playlist(playlist_id)
    # Now you can use the playlist data as needed
    st.write("Playlist Name:", playlist["name"])
    st.write("Total Tracks:", playlist["tracks"]["total"])
    # You can continue with your analysis using the playlist data
else:
    st.write("Please enter a valid Spotify playlist link.")


if playlist_id:
    playlist = sp.playlist(playlist_id)
    tracks = playlist["tracks"]["items"]
    track_names = [track["track"]["name"] for track in tracks]
    track_artists = [", ".join([artist["name"] for artist in track["track"]["artists"]]) for track in tracks]
    track_popularity = [track["track"]["popularity"] for track in tracks]
    track_duration = [track["track"]["duration_ms"] for track in tracks]
    track_album = [track["track"]["album"]["name"] for track in tracks]
    track_release_date = [track["track"]["album"]["release_date"] for track in tracks]

# display the playlist data in a table
    st.write(f"## {playlist['name']}")
    st.write(f"**Description:** {playlist['description']}")
    st.write(f"**Number of tracks:** {len(tracks)}")
    st.write("")
    st.write("### Tracklist")
    st.write("| Name | Artist | Album | Release Date | Popularity | Duration (ms) |")
    st.write("| ---- | ------ | ----- | ------------ | ---------- | -------------- |")
    for i in range(len(tracks)):
        st.write(f"| {track_names[i]} | {track_artists[i]} | {track_album[i]} | {track_release_date[i]} | {track_popularity[i]} | {track_duration[i]} |")

        # create a dataframe from the playlist data
        data = {"Name": track_names, "Artist": track_artists, "Album": track_album, "Release Date": track_release_date,
                "Popularity": track_popularity, "Duration (ms)": track_duration}
        df = pd.DataFrame(data)

# display a histogram of track popularity
    fig_popularity = px.histogram(df, x="Popularity", nbins=20, title="Track Popularity Distribution")
    st.plotly_chart(fig_popularity)

# add a dropdown menu for bivariate analysis
    st.write("#### Bivariate Analysis")
    x_axis = st.selectbox("Select a variable for the x-axis:", ["Popularity", "Duration (ms)"])
    y_axis = st.selectbox("Select a variable for the y-axis:", ["Popularity", "Duration (ms)"])
    fig_bivariate = px.scatter(df, x=x_axis, y=y_axis, title=f"{x_axis} vs. {y_axis}")
    st.plotly_chart(fig_bivariate)

# add a dropdown menu for multivariate analysis
    st.write("#### Multivariate Analysis")
    color_by = st.selectbox("Select a variable to color by:", ["Artist", "Album", "Release Date"])
    size_by = st.selectbox("Select a variable to size by:", ["Popularity", "Duration (ms)"])
    fig_multivariate = px.scatter(df, x="Duration (ms)", y="Popularity", color=color_by, size=size_by, hover_name="Name", title="Duration vs. Popularity Colored by Artist")
    st.plotly_chart(fig_multivariate)

# add a summary of the playlist data
    st.write("")
    st.write("### Playlist Summary")
    st.write(f"**Most popular track:** {df.iloc[df['Popularity'].idxmax()]['Name']} by {df.iloc[df['Popularity'].idxmax()]['Artist']} ({df['Popularity'].max()} popularity)")
    st.write(f"**Least popular track:** {df.iloc[df['Popularity'].idxmin()]['Name']} by {df.iloc[df['Popularity'].idxmin()]['Artist']} ({df['Popularity'].min()} popularity)")
# display a bar chart of the top 10 most popular artists in the playlist
    st.write("#### Top 10 Artists")
    st.write("The bar chart below shows the top 10 most popular artists in the playlist.")
    # Convert "Popularity" column to numeric data type
    df["Popularity"] = pd.to_numeric(df["Popularity"], errors="coerce")

    # Group by "Artist" and calculate the mean of "Popularity"
    top_artists = df.groupby("Artist")["Popularity"].mean().sort_values(ascending=False).head(10)

    # Plot the top 10 artists
    fig_top_artists = px.bar(x=top_artists.index, y=top_artists.values, title="Top 10 Artists")
    st.plotly_chart(fig_top_artists)

    # display a bar chart of the top 10 most popular songs in the playlist
    st.write("#### Top 10 Songs")
    st.write("The bar chart below shows the top 10 most popular songs in the playlist.")
    top_songs = df.groupby("Name")["Popularity"].mean().sort_values(ascending=False).head(10)
    fig_top_artistss = px.bar(x=top_songs.index, y=top_songs.values, title="Top 10 Songs")
    st.plotly_chart(fig_top_artistss)