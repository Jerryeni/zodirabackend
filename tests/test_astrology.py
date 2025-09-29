from datetime import date
from src.astrology_engine import VedicAstrologyEngine, PredictionEngine
from src.schemas import PersonProfile

def test_calculate_guna_milan():
    male = PersonProfile(
        id="1",
        user_id="u1",
        name="John",
        birth_date=date(1990, 1, 1),
        gender="male"
    )
    female = PersonProfile(
        id="2",
        user_id="u2",
        name="Jane",
        birth_date=date(1992, 1, 1),
        gender="female"
    )

    result = VedicAstrologyEngine.calculate_guna_milan(male, female)

    assert "total_guna" in result
    assert "compatibility_score" in result
    assert "details" in result
    assert "recommendation" in result
    assert result["total_guna"] == 36
    assert isinstance(result["compatibility_score"], int)

def test_get_daily_prediction():
    profile = PersonProfile(
        id="1",
        user_id="u1",
        name="John",
        birth_date=date(1990, 1, 1),
        gender="male"
    )

    result = PredictionEngine.get_daily_prediction(profile)

    assert "prediction" in result
    assert "lucky_color" in result
    assert "lucky_number" in result
    assert "favorable_activities" in result

def test_get_weekly_prediction():
    profile = PersonProfile(
        id="1",
        user_id="u1",
        name="John",
        birth_date=date(1990, 1, 1),
        gender="male"
    )

    result = PredictionEngine.get_weekly_prediction(profile)

    assert "prediction" in result
    assert "lucky_color" in result
    assert "lucky_number" in result
    assert "favorable_activities" in result

def test_get_monthly_prediction():
    profile = PersonProfile(
        id="1",
        user_id="u1",
        name="John",
        birth_date=date(1990, 1, 1),
        gender="male"
    )

    result = PredictionEngine.get_monthly_prediction(profile)

    assert "prediction" in result
    assert "lucky_color" in result
    assert "lucky_number" in result
    assert "favorable_activities" in result