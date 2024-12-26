import geopandas as gpd
import json
import requests
import streamlit as st
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim


def get_weather(lat, lon, api_key):
    """Fetch weather data from OpenWeatherMap API."""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def main():
    st.title("Earthquakes, Tsunamis, and Weather Visualization")

    # Input for OpenWeatherMap API key
    api_key = st.text_input("Enter OpenWeatherMap API key:", type="password")

    if not api_key:
        st.warning("Please enter an API key to get weather data")
        return

    # Load earthquake and tsunami data
    gdf_earthquakes = gpd.read_file("C:/Users/sef/Desktop/PythonProject/database.shp")
    gdf_tsunamis = gpd.read_file("C:/Users/sef/Desktop/PythonProject/sources.shp")  # Tsunami dataset

    # Load GeoJSON for countries
    url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
    response = requests.get(url)
    countries = json.loads(response.text)

    # Extract country names for dropdown
    country_names = [feature["properties"]["name"] for feature in countries["features"]]
    selected_country = st.selectbox("Select a country:", [""] + country_names)

    # Create folium map
    m = folium.Map(location=[0, 0], zoom_start=2)

    # Add country boundaries to map
    for feature in countries["features"]:
        country_name = feature["properties"]["name"]
        geom = feature["geometry"]

        folium.GeoJson(
            {"type": "Feature", "geometry": geom, "properties": {"name": country_name}},
            style_function=lambda x: {
                "fillColor": "#ffaf00",
                "fillOpacity": 0.1,
                "color": "black",
                "weight": 1,
            },
            tooltip=country_name,
            popup=folium.Popup(country_name, parse_html=True),
        ).add_to(m)

    # Render the map in Streamlit
    folium_static(m)

    # If a country is selected, fetch and display relevant data
    if selected_country:
        geolocator = Nominatim(user_agent="my_weather_app")
        location = geolocator.geocode(selected_country)

        if location:
            # Get weather data
            weather_data = get_weather(location.latitude, location.longitude, api_key)
            if weather_data and weather_data.get("main"):
                st.write(
                    f"""
                    ### Weather in {selected_country}:
                    - **Temperature**: {weather_data['main']['temp']}°C
                    - **Humidity**: {weather_data['main']['humidity']}%
                    - **Conditions**: {weather_data['weather'][0]['description']}
                    - **Wind Speed**: {weather_data['wind']['speed']} m/s
                    """
                )

            # Filter earthquakes within the selected area
            point = gpd.GeoSeries(
                gpd.points_from_xy([location.longitude], [location.latitude])
            )
            buffered_area = point.buffer(50)  # Adjust buffer size for area

            # Filter earthquakes
            earthquakes_in_area = gdf_earthquakes[
                gdf_earthquakes.geometry.within(buffered_area[0])
            ]

            if not earthquakes_in_area.empty:
                earthquakes_in_area["latitude"] = earthquakes_in_area.geometry.y
                earthquakes_in_area["longitude"] = earthquakes_in_area.geometry.x

                st.write("### Earthquakes in the Selected Area:")
                st.map(earthquakes_in_area[["latitude", "longitude"]])
            else:
                st.info("No earthquakes found in the selected area.")

            # Filter tsunamis within the selected area
            tsunamis_in_area = gdf_tsunamis[
                gdf_tsunamis.geometry.within(buffered_area[0])
            ]

            if not tsunamis_in_area.empty:
                tsunamis_in_area["latitude"] = tsunamis_in_area.geometry.y
                tsunamis_in_area["longitude"] = tsunamis_in_area.geometry.x

                st.write("### Tsunamis in the Selected Area:")
                st.map(tsunamis_in_area[["latitude", "longitude"]])
            else:
                st.info("No tsunamis found in the selected area.")
        else:
            st.error("Could not find coordinates for this country")


if __name__ == "__main__":
    main()
