from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from src.f1_data import get_race_weekends_by_year
from src.f1_data import (
    load_session, get_race_telemetry, get_driver_colors,
    get_circuit_rotation, enable_cache, optimize_frames_for_api,
)
 
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
enable_cache()

CURRENT_SEASON = date.today().year
 
@app.get("/api/race-telemetry/{year}/{round_number}/{session_type}")
def race_telemetry(year: int, round_number: int, session_type: str = "R", fps: int = 2):
    try:
        session = load_session(year, round_number, session_type)
        result = get_race_telemetry(session, session_type=session_type)
        colors = get_driver_colors(session)
        return {
            "event_name": session.event["EventName"],
            "telemetry": optimize_frames_for_api(result["frames"], colors, target_fps=fps),
            "track_statuses": result["track_statuses"],
            "total_laps": result["total_laps"],
            "driver_colors": colors,
            "circuit_rotation": get_circuit_rotation(session),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/circuits")
def circuits():
    """List this season's races only, for the picker UI."""
    weekends = get_race_weekends_by_year(CURRENT_SEASON)
    return {"year": CURRENT_SEASON, "races": weekends}
 
@app.get("/api/circuit-shape/{round_number}")
def circuit_shape(round_number: int, session_type: str = "R"):
    # Change your load_session logic to ONLY load laps, not telemetry or weather
    session = load_session(CURRENT_SEASON, round_number, session_type)
    
    # IMPORTANT: If your load_session function calls session.load() internally, 
    # make sure it only loads 'laps'. 
    # For a circuit shape, you don't need telemetry=True or weather=True.
    session.load(laps=True, telemetry=False, weather=False) 
    
    fastest = session.laps.pick_fastest()
    tel = fastest.get_telemetry() # This gets telemetry for ONLY one lap
    xs = tel["X"].to_numpy()[::5].round(1).tolist()
    ys = tel["Y"].to_numpy()[::5].round(1).tolist()
    return {
        "event_name": session.event["EventName"],
        "round": round_number,
        "rotation": get_circuit_rotation(session),
        "x": xs, "y": ys,
    }
 
@app.get("/api/race-telemetry/{round_number}/{session_type}")
def race_telemetry(round_number: int, session_type: str = "R", fps: int = 2):
    # year is no longer a path param — always current season
    try:
        session = load_session(CURRENT_SEASON, round_number, session_type)
        result = get_race_telemetry(session, session_type=session_type)
        colors = get_driver_colors(session)
        return {
            "event_name": session.event["EventName"],
            "telemetry": optimize_frames_for_api(result["frames"], colors, target_fps=fps),
            "track_statuses": result["track_statuses"],
            "race_control_messages": result["race_control_messages"],
            "total_laps": result["total_laps"],
            "driver_colors": colors,
            "circuit_rotation": get_circuit_rotation(session),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
