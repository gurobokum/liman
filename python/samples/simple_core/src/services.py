import random


class LocationService:
    """
    Resolves the current user's location.
    In a real app this would read from session, IP lookup, or user profile.
    """

    def __init__(self, location: str) -> None:
        self._location = location

    def get_current(self) -> str:
        return self._location


LOCATIONS = ["London", "Tokyo", "Moscow", "Barcelona", "New York", "Sydney", "Atlantis"]


def get_location_service() -> LocationService:
    return LocationService(location=random.choice(LOCATIONS))
