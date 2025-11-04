from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool
from livekit.plugins import noise_cancellation, silero

import openmeteo_requests
import requests_cache
from retry_requests import retry

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            You can provide weather information for a location using the get_weather tool.
            You can geocode a location name to get its coordinates using the geocode_location tool.
            If you are asked to provide weather information for a location, you should first geocode the location to get its coordinates using the geocode_location tool.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )
        # Setup Open-Meteo API client with cache and retry
        self.cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(self.cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)

    @function_tool
    async def geocode_location(self, location: str) -> dict:
        """
        Converts a location name to geographic coordinates using Open-Meteo Geocoding API.

        Args:
            location: The location name to geocode (e.g., "Rome", "New York", "London")

        Returns:
            A dictionary with latitude, longitude, and location name, or None if not found
        """
        try:
            logger.info(f"Geocoding location: {location}")
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            response = self.cache_session.get(geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                coords = {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result.get("name", location),
                    "country": result.get("country", ""),
                    "admin1": result.get("admin1", "")
                }
                logger.info(f"Found coordinates for {location}: {coords['latitude']}, {coords['longitude']}")
                return coords
            else:
                logger.warning(f"No coordinates found for location: {location}")
                return {"latitude": None, "longitude": None, "name": None, "country": None, "admin1": None}
        except Exception as e:
            logger.error(f"Error geocoding location {location}: {e}")
            return {"latitude": None, "longitude": None, "name": None, "country": None, "admin1": None}

    @function_tool
    async def get_weather(self, latitude: float, longitude: float) -> str:
        """
        Gets today's weather forecast for a location using Open-Meteo API.
        First geocodes the location to get coordinates, then fetches weather data.

        Args:
            location: The location to get the weather for (e.g., "Rome", "New York")
        """
        try:
            logger.info(f"Getting weather for {latitude}, {longitude}")
            
            # Make the weather API request
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m"],
                "timezone": "auto",
            }
            
            responses = self.openmeteo.weather_api(url, params=params)
            response = responses[0]
            
            # Process current weather data
            current = response.Current()
            current_temperature_2m = current.Variables(0).Value()
            current_relative_humidity_2m = current.Variables(1).Value()
            current_weather_code = current.Variables(2).Value()
            current_wind_speed_10m = current.Variables(3).Value()
            
            # Weather code descriptions (simplified)
            weather_descriptions = {
                0: "clear sky",
                1: "mainly clear",
                2: "partly cloudy",
                3: "overcast",
                45: "foggy",
                48: "depositing rime fog",
                51: "light drizzle",
                53: "moderate drizzle",
                55: "dense drizzle",
                56: "light freezing drizzle",
                57: "dense freezing drizzle",
                61: "slight rain",
                63: "moderate rain",
                65: "heavy rain",
                71: "slight snow fall",
                73: "moderate snow fall",
                75: "heavy snow fall",
                77: "snow grains",
                80: "slight rain showers",
                81: "moderate rain showers",
                82: "violent rain showers",
                85: "slight snow showers",
                86: "heavy snow showers",
                95: "thunderstorm",
                96: "thunderstorm with slight hail",
                99: "thunderstorm with heavy hail"
            }
            
            weather_desc = weather_descriptions.get(int(current_weather_code), "unknown")

            result = (
                f"The weather at {latitude}, {longitude} is {weather_desc} "
                f"with a temperature of {current_temperature_2m:.1f} degrees Celsius, "
                f"humidity at {current_relative_humidity_2m:.0f} percent, "
                f"and wind speed of {current_wind_speed_10m:.1f} kilometers per hour."
            )
            
            logger.info(f"Weather retrieved successfully for {latitude}, {longitude}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting weather for {latitude}, {longitude}: {e}")
            return f"Sorry, I couldn't retrieve the weather for {latitude}, {longitude}. Please try again later."


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4o-mini",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))