# Stride - Voice Running Coach

A voice-first AI running coach that helps you log training, plan workouts, and prepare for races.

## Demo

🔗 [Live Demo](https://stride-coach.up.railway.app/)

## Why I Built This

I run 30+ miles a week and lead UCSD's Strides Running Club (largest running club in the UC system). Runners want to log runs immediately after finishing - when your hands are sweaty and you're catching your breath. Voice is the natural interface.

The core insight: **running is already a voice-friendly activity**. You can talk while running (if you're going easy enough). You want hands-free interaction post-run. And the data you're logging is conversational - "I did 6 miles today, felt pretty good but my calf was tight."

## How to Use

1. Click the microphone button
2. Say something like:
   - "I just ran 5 miles in 45 minutes"
   - "What's the weather like?"
   - "How's my week going?"
   - "What should I run tomorrow?"
   - "Set a goal for a half marathon on March 15th"
3. See your training log update in real-time

## Product Decisions

### Opinionated Scope
This is a running coach, not a generic assistant. It knows about pacing, training load, recovery, and race preparation. That specificity makes it more useful than a general-purpose voice bot.

### Proactive Logging
When you mention completing a run, Stride logs it automatically. No "would you like me to save that?" - it just does it and confirms. This matches how you'd talk to a human coach.

### Context That Matters
Stride remembers:
- Your injury history ("Last week you mentioned your knee was bothering you")
- Your goals ("You've got the LA Marathon in 8 weeks")
- Your training patterns ("You've done 25 miles this week already")

This context makes the advice relevant, not generic.

### Function Calls as Product Features
I used function calling not just to retrieve data, but to take meaningful actions:

| Function | What it Does | Why it Matters |
|----------|--------------|----------------|
| `log_run` | Records completed runs | Core value prop - voice-based logging |
| `get_weekly_summary` | Training load context | Informs recovery/intensity advice |
| `get_weather` | Current conditions | Practical run planning |
| `set_goal` | Race goal tracking | Enables training periodization |
| `suggest_workout` | Context-aware recommendations | Adapts to your current fitness |
| `get_past_context` | Search conversation history | True continuity across sessions |
| `get_running_history` | Recent training data | Shows patterns over 2 weeks |
| `get_goals` | View upcoming races | Keeps goals top of mind |

## Technical Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  React Frontend │◄──────────────────►│  FastAPI Server │
│  + Web Audio    │                    │                 │
└─────────────────┘                    └────────┬────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
               ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
               │ OpenAI Realtime │    │     SQLite      │    │  Weather API    │
               │      API        │    │                 │    │                 │
               └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Tech Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python + FastAPI
- **Database**:  SQLite
- **Voice**: OpenAI Realtime API (speech-to-speech)
- **Deployment**: Railway

### Key Technical Decisions

**WebSocket for real-time audio**: The OpenAI Realtime API uses WebSockets for streaming audio. I pipe audio from the browser's MediaStream API directly to OpenAI, and stream responses back for playback. This keeps latency low.

**Server-side function execution**: Functions run on the backend where they have database access. When OpenAI calls a function, my server executes it and returns results, then triggers a follow-up response.

**Conversation persistence**: Every message (user and assistant) is stored with timestamps. This enables the `get_past_context` function to search history and provide continuity.

## Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key with Realtime API access

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run server
python main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open http://localhost:3000 in your browser.

## What I'd Build With More Time

1. **Strava Integration**: Import runs automatically, sync back logged runs
2. **Training Plans**: Generate periodized plans for specific races
3. **Injury Tracking**: Dedicated logging for pain/injury with recovery suggestions
4. **Social Features**: Share runs with training partners, group challenges
5. **Advanced Analytics**: Training load calculations (ATL/CTL), race predictions

## Project Structure

```
stride-coach/
├── backend/
│   ├── main.py           # FastAPI app + WebSocket handler
│   ├── database.py       # SQLAlchemy models
│   ├── functions.py      # Tool implementations
│   ├── prompts.py        # System prompt + tool definitions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── hooks/
│   │   │   └── useVoiceChat.js   # WebSocket + audio handling
│   │   └── components/
│   │       ├── VoiceButton.jsx
│   │       ├── ChatMessages.jsx
│   │       └── TrainingLog.jsx
│   └── package.json
└── README.md
```

## Author

Jonathan Ho  
[GitHub](https://github.com/jona-thanho) | [LinkedIn](https://linkedin.com/in/jonatuanho)

CS @ UC San Diego | Software Engineer @ Bettor Odds | President, Strides Running Club
