import httpx
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date, timedelta
from database import Run, Goal, Message, Conversation


async def log_run(
    db: Session,
    user_id: int,
    distance_miles: float,
    duration_minutes: int,
    notes: str = None,
    run_date: str = None
) -> dict:
    """Log a completed run to the training log."""
    
    # Calculate pace
    if distance_miles > 0:
        pace_decimal = duration_minutes / distance_miles
        pace_minutes = int(pace_decimal)
        pace_seconds = int((pace_decimal - pace_minutes) * 60)
        pace_formatted = f"{pace_minutes}:{pace_seconds:02d}"
    else:
        pace_formatted = "N/A"
    
    # Parse date
    if run_date:
        try:
            parsed_date = datetime.strptime(run_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = date.today()
    else:
        parsed_date = date.today()
    
    # Create run record
    run = Run(
        user_id=user_id,
        distance_miles=distance_miles,
        duration_minutes=duration_minutes,
        pace_per_mile=pace_formatted,
        notes=notes,
        run_date=parsed_date
    )
    
    db.add(run)
    db.commit()
    
    return {
        "success": True,
        "message": f"Logged {distance_miles} miles in {duration_minutes} minutes ({pace_formatted}/mile)",
        "run_id": run.id,
        "pace": pace_formatted
    }


async def get_weekly_summary(db: Session, user_id: int) -> dict:
    """Get summary of runs from the past 7 days."""
    
    week_ago = date.today() - timedelta(days=7)
    
    runs = db.query(Run).filter(
        Run.user_id == user_id,
        Run.run_date >= week_ago
    ).order_by(desc(Run.run_date)).all()
    
    if not runs:
        return {
            "total_miles": 0,
            "total_minutes": 0,
            "num_runs": 0,
            "message": "No runs logged in the past 7 days."
        }
    
    total_miles = sum(r.distance_miles for r in runs)
    total_minutes = sum(r.duration_minutes for r in runs)
    
    runs_data = [
        {
            "date": r.run_date.strftime("%A, %b %d"),
            "distance": r.distance_miles,
            "duration": r.duration_minutes,
            "pace": r.pace_per_mile,
            "notes": r.notes
        }
        for r in runs
    ]
    
    return {
        "total_miles": round(total_miles, 1),
        "total_minutes": total_minutes,
        "num_runs": len(runs),
        "average_pace": f"{int(total_minutes/total_miles)}:{int((total_minutes/total_miles % 1) * 60):02d}" if total_miles > 0 else "N/A",
        "runs": runs_data
    }


async def get_running_history(db: Session, user_id: int, days: int = 14) -> dict:
    """Get recent runs to understand training patterns."""
    
    start_date = date.today() - timedelta(days=days)
    
    runs = db.query(Run).filter(
        Run.user_id == user_id,
        Run.run_date >= start_date
    ).order_by(desc(Run.run_date)).all()
    
    if not runs:
        return {
            "total_miles": 0,
            "num_runs": 0,
            "message": f"No runs logged in the past {days} days."
        }
    
    total_miles = sum(r.distance_miles for r in runs)
    
    runs_data = [
        {
            "date": r.run_date.strftime("%Y-%m-%d"),
            "distance": r.distance_miles,
            "duration": r.duration_minutes,
            "pace": r.pace_per_mile,
            "notes": r.notes
        }
        for r in runs
    ]
    
    return {
        "period_days": days,
        "total_miles": round(total_miles, 1),
        "num_runs": len(runs),
        "avg_miles_per_week": round(total_miles / (days / 7), 1),
        "runs": runs_data
    }


async def get_weather(location: str = "San Diego") -> dict:
    """Get current weather for run planning."""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://wttr.in/{location}?format=j1"
            )
            response.raise_for_status()
            data = response.json()
            current = data["current_condition"][0]
            
            return {
                "location": location,
                "temp_f": current["temp_F"],
                "feels_like_f": current["FeelsLikeF"],
                "humidity": current["humidity"],
                "conditions": current["weatherDesc"][0]["value"],
                "wind_mph": current["windspeedMiles"]
            }
    except Exception as e:
        return {
            "error": f"Could not fetch weather: {str(e)}",
            "location": location
        }


async def set_goal(
    db: Session,
    user_id: int,
    race_name: str,
    race_date: str,
    distance_miles: float,
    target_time: str = None
) -> dict:
    """Set or update a race goal."""
    
    try:
        parsed_date = datetime.strptime(race_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}
    
    goal = Goal(
        user_id=user_id,
        race_name=race_name,
        race_date=parsed_date,
        target_time=target_time,
        distance_miles=distance_miles
    )
    
    db.add(goal)
    db.commit()
    
    days_until = (parsed_date - date.today()).days
    
    return {
        "success": True,
        "message": f"Goal set: {race_name} ({distance_miles} miles) on {parsed_date.strftime('%B %d, %Y')}",
        "target_time": target_time,
        "days_until_race": days_until,
        "weeks_until_race": round(days_until / 7, 1)
    }


async def get_goals(db: Session, user_id: int) -> dict:
    """Get user's current race goals."""
    
    goals = db.query(Goal).filter(
        Goal.user_id == user_id,
        Goal.race_date >= date.today()
    ).order_by(Goal.race_date).all()
    
    if not goals:
        return {"message": "No upcoming race goals set.", "goals": []}
    
    goals_data = [
        {
            "race_name": g.race_name,
            "race_date": g.race_date.strftime("%B %d, %Y"),
            "distance_miles": g.distance_miles,
            "target_time": g.target_time,
            "days_until": (g.race_date - date.today()).days
        }
        for g in goals
    ]
    
    return {"goals": goals_data}


async def suggest_workout(
    db: Session,
    user_id: int,
    workout_type: str = None
) -> dict:
    """Suggest a workout based on goals and recent training."""
    
    # Get recent training context
    summary = await get_weekly_summary(db, user_id)
    goals_data = await get_goals(db, user_id)
    
    weekly_miles = summary.get("total_miles", 0)
    num_runs = summary.get("num_runs", 0)
    
    # Auto-suggest workout type if not specified
    if not workout_type:
        if num_runs == 0:
            workout_type = "easy"
        elif weekly_miles > 30:
            workout_type = "recovery"
        elif num_runs < 3:
            workout_type = "easy"
        else:
            workout_type = "easy"  # Default to easy
    
    suggestions = {
        "easy": {
            "name": "Easy Run",
            "description": f"4-5 miles at a comfortable, conversational pace. Based on your {weekly_miles} miles this week, keep it relaxed.",
            "duration": "35-45 minutes",
            "intensity": "Low - you should be able to hold a conversation"
        },
        "tempo": {
            "name": "Tempo Run",
            "description": "Warm up 1 mile easy, then 3 miles at tempo pace (comfortably hard), cool down 1 mile easy.",
            "duration": "45-50 minutes",
            "intensity": "Medium-high - challenging but sustainable"
        },
        "intervals": {
            "name": "Interval Workout",
            "description": "Warm up 1 mile, then 6x800m at 5K effort with 400m recovery jog between each, cool down 1 mile.",
            "duration": "50-55 minutes",
            "intensity": "High - these should feel hard"
        },
        "long_run": {
            "name": "Long Run",
            "description": f"8-10 miles at easy pace. You've done {weekly_miles} miles so far this week, so pace yourself for the distance.",
            "duration": "70-90 minutes",
            "intensity": "Low - building endurance, not speed"
        },
        "recovery": {
            "name": "Recovery Run",
            "description": f"Easy 3-4 miles, very relaxed pace. You've got {weekly_miles} miles this week already - this is about active recovery.",
            "duration": "25-35 minutes",
            "intensity": "Very low - slower than you think"
        }
    }
    
    workout = suggestions.get(workout_type, suggestions["easy"])
    workout["weekly_context"] = f"{weekly_miles} miles across {num_runs} runs this week"
    
    if goals_data.get("goals"):
        next_goal = goals_data["goals"][0]
        workout["goal_context"] = f"Training for {next_goal['race_name']} in {next_goal['days_until']} days"
    
    return workout


async def get_past_context(db: Session, user_id: int, query: str) -> dict:
    """Search past conversations for relevant context."""
    
    # Get user's conversations
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).all()
    
    if not conversations:
        return {"message": "No past conversations found.", "results": []}
    
    conv_ids = [c.id for c in conversations]
    
    # Simple keyword search in messages
    messages = db.query(Message).filter(
        Message.conversation_id.in_(conv_ids),
        Message.content.ilike(f"%{query}%")
    ).order_by(desc(Message.created_at)).limit(5).all()
    
    if not messages:
        return {"message": f"No mentions of '{query}' found in past conversations.", "results": []}
    
    results = [
        {
            "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
            "role": m.role,
            "date": m.created_at.strftime("%B %d, %Y")
        }
        for m in messages
    ]
    
    return {
        "query": query,
        "num_results": len(results),
        "results": results
    }


# Function dispatcher
FUNCTION_MAP = {
    "log_run": log_run,
    "get_weekly_summary": get_weekly_summary,
    "get_running_history": get_running_history,
    "get_weather": get_weather,
    "set_goal": set_goal,
    "get_goals": get_goals,
    "suggest_workout": suggest_workout,
    "get_past_context": get_past_context,
}


async def execute_function(db: Session, user_id: int, function_name: str, arguments: dict) -> dict:
    """Execute a function by name with given arguments."""
    
    func = FUNCTION_MAP.get(function_name)
    if not func:
        return {"error": f"Unknown function: {function_name}"}
    
    # Functions that need db and user_id
    db_functions = ["log_run", "get_weekly_summary", "get_running_history", 
                    "set_goal", "get_goals", "suggest_workout", "get_past_context"]
    
    try:
        if function_name in db_functions:
            return await func(db, user_id, **arguments)
        else:
            return await func(**arguments)
    except Exception as e:
        return {"error": f"Error executing {function_name}: {str(e)}"}