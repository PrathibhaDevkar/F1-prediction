from fastapi import APIRouter

from services import fastf1_service

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
        }
        for _, row in lineup.iterrows()
    ]
    teams = sorted({d["team"] for d in drivers})

    return {"season": season, "drivers": drivers, "teams": teams}
