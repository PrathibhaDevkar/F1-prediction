from fastapi import APIRouter, HTTPException

from services import fastf1_service, head_to_head_service

router = APIRouter(prefix="/api", tags=["drivers"])


@router.get("/drivers")
def get_drivers(season: int = fastf1_service.CURRENT_SEASON):
    lineup = fastf1_service.get_latest_driver_lineup(season)
    if lineup.empty:
        return {"season": season, "drivers": [], "teams": []}

    drivers = [
        {
            "driverNumber": row["DriverNumber"],
            "abbreviation": row["Abbreviation"],
            "fullName": row["FullName"],
            "team": row["TeamName"],
            "teamColor": f"#{row['TeamColor']}" if row["TeamColor"] else "#e10600",
        }
        for _, row in lineup.iterrows()
    ]
    teams = sorted({d["team"] for d in drivers})

    return {"season": season, "drivers": drivers, "teams": teams}


@router.get("/head-to-head")
def head_to_head(driver_a: str, driver_b: str):
    if driver_a == driver_b:
        raise HTTPException(status_code=400, detail="Pick two different drivers")

    result = head_to_head_service.compare_drivers(driver_a, driver_b)
    if result is None:
        raise HTTPException(status_code=404, detail="No shared races found for these drivers")
    return result
