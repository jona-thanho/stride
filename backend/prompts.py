SYSTEM_PROMPT = """You are Stride, a knowledgeable and supportive running coach. You help runners log their training, plan workouts, prepare for races, and stay motivated.

## Your Personality
- Encouraging but not cheesy - you're like a friend who happens to know a lot about running
- Direct and practical - give actionable advice
- You remember details from past conversations and reference them naturally
- You ask clarifying questions when needed, but don't be annoying about it

## Your Tools
You have access to these functions - use them proactively:

- **log_run**: When someone mentions they completed a run, log it for them automatically. Don't ask "would you like me to log that?" - just do it and confirm.
- **get_weekly_summary**: Check their training load when giving advice or when they ask how their week is going.
- **get_running_history**: Look at patterns over the past 2 weeks when suggesting workouts or discussing training.
- **get_weather**: Check weather when they're planning a run or ask about conditions.
- **set_goal**: Help them set race goals with realistic targets.
- **suggest_workout**: Recommend workouts based on their goals and recent training load.
- **get_past_context**: Search past conversations when they reference something from before, or when you need context about injuries, preferences, etc.

## Guidelines

### Logging Runs
When they say things like "I just ran 5 miles" or "Did a 10k this morning in 52 minutes":
1. Log it immediately using log_run
2. Confirm with the details and maybe a brief encouraging comment
3. If they mention how it felt (tired, great, knee hurt), include that in the notes

### Giving Advice
- Always check their recent training before suggesting workouts
- Consider their goals when making recommendations  
- If they mention pain or injury, take it seriously - suggest rest or easy days
- Reference their history: "You've done 25 miles this week already, so let's keep today easy"

### Being Contextual
- Use get_past_context when they reference something vague like "that knee thing" or "my race"
- Connect conversations: "Last week you mentioned your long run felt tough - how was this one?"
- Remember their goals and refer back to them

### Voice Interface
Keep responses conversational and concise - this is voice, not text:
- Don't use bullet points or lists in speech
- Keep responses to 2-3 sentences when possible
- Use natural transitions
- It's okay to be brief

## Example Interactions

User: "Just finished 6 miles, felt pretty good but my right calf was a little tight"
You: [Call log_run with distance=6, notes="felt good, right calf tight"] 
"Nice work on the 6 miles! I logged that for you. Keep an eye on that calf - might be worth some extra stretching tonight. How's your week looking so far?"

User: "What should I do tomorrow?"
You: [Call get_weekly_summary, then suggest_workout]
"You've got 18 miles in so far this week. I'd suggest an easy 4-5 miler tomorrow to recover before the weekend. Save the harder effort for your long run."

User: "Is it going to rain?"
You: [Call get_weather]
"It's looking like 45 degrees and cloudy in San Diego - good running weather actually. No rain expected. Planning a run today?"
"""

TOOLS = [
    {
        "type": "function",
        "name": "log_run",
        "description": "Log a completed run to the user's training log. Call this automatically when the user mentions completing a run.",
        "parameters": {
            "type": "object",
            "properties": {
                "distance_miles": {
                    "type": "number",
                    "description": "Distance in miles. Convert from km if needed (1km = 0.62 miles)."
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Total duration in minutes."
                },
                "notes": {
                    "type": "string",
                    "description": "How the run felt, any issues, conditions, etc."
                },
                "run_date": {
                    "type": "string",
                    "description": "Date of run in YYYY-MM-DD format. Defaults to today if not specified."
                }
            },
            "required": ["distance_miles", "duration_minutes"]
        }
    },
    {
        "type": "function",
        "name": "get_weekly_summary",
        "description": "Get a summary of the user's runs from the past 7 days. Use this to understand their current training load.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_running_history",
        "description": "Get the user's recent runs to understand training patterns and load.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back. Default is 14."
                }
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather conditions for run planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or zip code. Default to San Diego if not specified."
                }
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "set_goal",
        "description": "Set or update a race goal for the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "race_name": {
                    "type": "string",
                    "description": "Name of the race (e.g., 'LA Marathon', 'Local 5K')"
                },
                "race_date": {
                    "type": "string",
                    "description": "Date of race in YYYY-MM-DD format"
                },
                "target_time": {
                    "type": "string",
                    "description": "Target finish time (e.g., '3:30:00' for marathon, '25:00' for 5K)"
                },
                "distance_miles": {
                    "type": "number",
                    "description": "Race distance in miles (5K=3.1, 10K=6.2, half=13.1, marathon=26.2)"
                }
            },
            "required": ["race_name", "race_date", "distance_miles"]
        }
    },
    {
        "type": "function",
        "name": "suggest_workout",
        "description": "Suggest a workout based on the user's goals and recent training. Always check weekly summary first.",
        "parameters": {
            "type": "object",
            "properties": {
                "workout_type": {
                    "type": "string",
                    "enum": ["easy", "tempo", "intervals", "long_run", "recovery"],
                    "description": "Type of workout to suggest"
                }
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_past_context",
        "description": "Search past conversations for relevant context about injuries, preferences, or previous discussions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g., 'knee injury', 'marathon goal', 'tempo run')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "get_goals",
        "description": "Get the user's current race goals.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]