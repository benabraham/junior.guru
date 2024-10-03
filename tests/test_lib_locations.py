from operator import itemgetter

import pytest

from jg.coop.lib.locations import fetch_locations, get_region, optimize_geocoding


@pytest.mark.parametrize(
    "locations_raw, address, expected",
    [
        (
            ["252 30 Řevnice, Česko"],
            {"place": "Řevnice", "region": "Středočeský kraj", "country": "Česko"},
            [{"name": "Řevnice", "region": "Praha"}],
        ),
        (
            ["Bočiar, Slovensko"],
            {"place": "Bočiar", "region": "Košický kraj", "country": "Slovensko"},
            [{"name": "Bočiar", "region": "Košice"}],
        ),
    ],
)
def test_locations(locations_raw: list[str], address: dict, expected: list[dict]):
    results = fetch_locations(locations_raw, geocode=lambda _: address)

    assert results == expected


def test_locations_remote():
    results = fetch_locations([], geocode=lambda _: {})

    assert results == []


def test_locations_no_response():
    results = fetch_locations(["???"], geocode=lambda _: None)

    assert results == []


def test_locations_multiple():
    addresses = iter(
        [
            {"place": "Řevnice", "region": "Středočeský kraj", "country": "Česko"},
            {"place": "Brno", "region": "Jihomoravský kraj", "country": "Česko"},
        ]
    )
    results = fetch_locations(
        ["252 30 Řevnice, Česko", "Brno, Česko"], geocode=lambda _: next(addresses)
    )

    assert sorted(results, key=itemgetter("name")) == [
        {"name": "Brno", "region": "Brno"},
        {"name": "Řevnice", "region": "Praha"},
    ]


def test_locations_multiple_no_response():
    addresses = iter(
        [None, {"place": "Brno", "region": "Jihomoravský kraj", "country": "Česko"}]
    )
    results = fetch_locations(["???", "Brno, Česko"], geocode=lambda _: next(addresses))

    assert results == [{"name": "Brno", "region": "Brno"}]


def test_locations_multiple_unique():
    addresses = iter(
        [
            {"place": "Brno", "region": "Jihomoravský kraj", "country": "Česko"},
            {"place": "Brno", "region": "Jihomoravský kraj", "country": "Česko"},
        ]
    )
    results = fetch_locations(
        ["Plevova 1, Brno, Česko", "Brno, Česko"], geocode=lambda _: next(addresses)
    )

    assert results == [{"name": "Brno", "region": "Brno"}]


def test_get_region_from_country():
    address = dict(region="Województwo Mazowieckie", country="Polska")

    assert get_region(address) == "Polsko"


@pytest.mark.parametrize(
    "region, country, expected",
    [
        ("Středočeský kraj", "Česko", "Praha"),
        ("Středočeský kraj", "Česká republika", "Praha"),
        ("Praha", "Česko", "Praha"),
        ("Praha", "Česká republika", "Praha"),
    ],
)
def test_get_region_from_region(region: str, country: str, expected: str):
    address = dict(region=region, country=country)

    assert get_region(address) == expected


GEOCODED_ADDRESS = {
    "place": "-- GEOCODED --",
    "region": "-- GEOCODED --",
    "country": "-- GEOCODED --",
}


@pytest.mark.parametrize(
    "location_raw, expected",
    [
        ("252 30 Řevnice, Česko", GEOCODED_ADDRESS),
        (
            "130 00 Praha 3-Žižkov",
            {"place": "Praha", "region": "Praha", "country": "Česko"},
        ),
        ("Prague, Czechia", {"place": "Praha", "region": "Praha", "country": "Česko"}),
        ("Brno-Žabovřesky", {"place": "Brno", "region": "Brno", "country": "Česko"}),
        (
            "Michálkovická 1137/197, 710 00 Ostrava - Slezská Ostrava, Czechia",
            {"place": "Ostrava", "region": "Ostrava", "country": "Česko"},
        ),
    ],
)
def test_optimize_geocoding(location_raw, expected):
    def geocode(location_raw):
        return GEOCODED_ADDRESS

    assert optimize_geocoding(geocode)(location_raw) == expected
