# LiveKit Voice Agent

An intelligent voice assistant built with LiveKit Agents that can answer questions and provide real-time weather information.

## Features

- **Voice AI Assistant**: Conversational voice assistant based on LiveKit Agents
- **Weather Forecasts**: Integration with Open-Meteo API to get real-time weather forecasts
- **Geocoding**: Tool to convert location names into geographic coordinates
- **Noise Cancellation**: Audio noise cancellation for clearer conversations
- **Caching**: API request caching to improve performance

## Technologies Used

### AI/ML
- **STT (Speech-to-Text)**: AssemblyAI Universal Streaming
- **LLM**: OpenAI GPT-4o-mini
- **TTS (Text-to-Speech)**: Cartesia Sonic-3
- **VAD (Voice Activity Detection)**: Silero VAD

### APIs and Services
- **Open-Meteo API**: For weather forecasts and geocoding
- **requests-cache**: HTTP request caching
- **retry-requests**: Automatic retry for failed requests

### Framework
- **LiveKit Agents**: Framework for voice AI agents
- **LiveKit Plugins**: Noise cancellation and other features

## Code Structure

### `Assistant` Agent

The `Assistant` class extends `Agent` and implements:

1. **`geocode_location(location: str)`**: Tool to convert location names into coordinates
   - Uses Open-Meteo geocoding API
   - Returns latitude, longitude, name, country, and region

2. **`get_weather(latitude: float, longitude: float)`**: Tool to get weather forecasts
   - Uses Open-Meteo forecast API
   - Returns temperature, humidity, weather conditions, and wind speed
   - Supports textual descriptions of weather codes

### Entrypoint

The `entrypoint` function configures the agent session with:
- STT, LLM, and TTS configured
- Noise cancellation enabled
- Automatic session lifecycle management

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment variables in `.env.local`:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
OPENAI_API_KEY=your-openai-key
```

3. Start the agent:
```bash
python agent.py
```

## Functionality

The agent can:
- Answer general questions using LLM knowledge
- Provide weather forecasts for any location
- Geocode location names to get coordinates
- Maintain natural and fluid conversations

## Notes

- API requests are cached for 1 hour to reduce the number of calls
- The system includes automatic retry to improve reliability
- Weather data is updated in real-time via Open-Meteo