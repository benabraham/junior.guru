import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Generator

import pytest
from peewee import SqliteDatabase
from strictyaml import load

from jg.coop.models.base import BaseModel, db as production_db


def prepare_test_db(models: list[BaseModel]) -> Generator[SqliteDatabase, None, None]:
    """
    Prepares a temporary in-memory SQLite database with the given models
    and the same custom functions as on the production database.
    """
    db = SqliteDatabase(":memory:")
    db._functions = dict(production_db._functions)  # copy functions
    with db.connection_context():
        db.bind(models)
        db.create_tables(models)
        yield db
        db.drop_tables(models)


def load_yaml(s, schema):
    """
    Uses json.loads/json.dumps to recursively convert all ordered dicts
    to dicts, which significantly improves readability of the pytest diff
    """
    return json.loads(json.dumps(load(s, schema).data))


def startswith_skip(path):
    """
    Tests whether the given path's basename starts with the word SKIP
    """
    return Path(path).name.lower().startswith("skip")


def param_startswith_skip(path, values=2):
    """
    Creates a @pytes.mark.parametrize() param, which is marked as skipped
    because the path startswith the word SKIP

    The 'values' parameter specifies how many value arguments the marker
    needs to fake so that pytest doesn't complain that the param doesn't fit
    the declared number of values. It's usually 2 (input and expected output),
    so 2 is the default.

    The skip reason can be displayed by running 'pytest -r s'
    """
    args = ["" for _ in range(values)]
    path_relative = path.relative_to(Path.cwd())
    marks = pytest.mark.skip(f"starts with SKIP: {path_relative}")
    return pytest.param(*args, id=Path(path).name, marks=marks)


def param_xfail_missing(path, values=2):
    """
    Creates a @pytes.mark.parametrize() param, which is marked as failed
    because of a fixture path missing

    The 'values' parameter specifies how many value arguments the marker
    needs to fake so that pytest doesn't complain that the param doesn't fit
    the declared number of values. It's usually 2 (input and expected output),
    so 2 is the default.

    The skip reason can be displayed by running 'pytest -r x'
    """
    args = ["" for _ in range(values)]
    path_relative = path.relative_to(Path.cwd())
    marks = pytest.mark.xfail(f"missing: {path_relative}")
    return pytest.param(*args, id=Path(path).name, marks=marks)


def prepare_job_data(id, **kwargs):
    return dict(
        id=str(id),
        posted_at=kwargs.get("posted_at", date(2019, 7, 6)),
        company_name=kwargs.get("company_name", "Honza Ltd."),
        employment_types=kwargs.get("employment_types", ["internship"]),
        title=kwargs.get("title", "Junior Software Engineer"),
        company_url=kwargs.get("company_url", "https://example.com"),
        email=kwargs.get("email", "recruiter@example.com"),
        remote=kwargs.get("remote", False),
        locations_raw=kwargs.get("locations_raw", ["Brno, Czech Republic"]),
        locations=kwargs.get("locations", [{"name": "Brno", "region": "Brno"}]),
        description_html=kwargs.get(
            "description", "<p><strong>Useful</strong> description.</p>"
        ),
        source=kwargs.get("source", random.choice(["juniorguru", "moo", "boo", "foo"])),
        expires_at=kwargs.get("expires_at", date.today() + timedelta(days=3)),
        junior_rank=kwargs.get("junior_rank", 10),
        sort_rank=kwargs.get("sort_rank", 5),
        lang=kwargs.get("lang", "en"),
        link=kwargs.get("link", "https://example.com/jobs/123/"),
        apply_link=kwargs.get("apply_link"),
        pricing_plan=kwargs.get("pricing_plan", "community"),
    )


def prepare_logo_data(id, **kwargs):
    today = date.today()
    return dict(
        id=id,
        name=kwargs.get("name", "Awesome Company"),
        filename=kwargs.get("filename", "awesome-company.svg"),
        email=kwargs.get("email", "recruitment@example.com"),
        email_reports=kwargs.get("email_reports", True),
        link=kwargs.get("link", "https://jobs.example.com"),
        link_re=kwargs.get("link_re"),
        months=kwargs.get("monhts", 12),
        starts_at=kwargs.get("starts_at", today),
        expires_at=kwargs.get("expires_at", today + timedelta(days=365)),
    )


def prepare_partner_data(id, **kwargs):
    return dict(
        id=id,
        slug=kwargs.pop("slug", f"banana{id}"),
        name=kwargs.pop("name", f"Banana #{id}"),
        logo_path=kwargs.pop("logo_path", "logos/banana.svg"),
        url=kwargs.pop("url", "https://banana.example.com"),
        coupon=kwargs.pop("coupon", "BANANA123123123"),
        **kwargs,
    )


def prepare_course_provider_data(id, **kwargs):
    return dict(
        id=id,
        name=kwargs.pop("name", "Test Course Provider"),
        slug=kwargs.pop("slug", f"test-course-provider-{id}"),
        url=kwargs.pop("url", "https://example.com"),
        edit_url=kwargs.pop("edit_url", "https://example.com/edit"),
        page_title=kwargs.pop("page_title", "Test Course Provider"),
        page_description=kwargs.pop("page_description", "Test Course Provider"),
        page_lead=kwargs.pop("page_lead", "Test Course Provider"),
        **kwargs,
    )
