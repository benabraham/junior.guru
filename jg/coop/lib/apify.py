import os
from datetime import timedelta

from apify_client import ApifyClient
from apify_shared.consts import ActorJobStatus

from jg.coop.lib import loggers
from jg.coop.lib.cache import cache


APIFY_API_KEY = os.getenv("APIFY_API_KEY")


logger = loggers.from_path(__file__)


@cache(expire=timedelta(days=1), tag="apify")
def fetch_data(
    actor_name: str,
    token: str | None = None,
    raise_if_missing: bool = True,
) -> list[dict]:
    client = ApifyClient(token=token or APIFY_API_KEY)

    logger.debug(f"Getting last successful run of {actor_name}")
    actor = client.actor(actor_name)
    last_run = actor.last_run(status=ActorJobStatus.SUCCEEDED)
    run_info = last_run.get()
    if run_info is None:
        if raise_if_missing:
            raise RuntimeError(f"No successful runs of {actor_name!r} found")
        logger.error(f"No successful runs of {actor_name!r} found")
        return []

    run_url = (
        f"https://console.apify.com/actors/{run_info['actId']}/runs/{run_info['id']}"
    )
    logger.debug(
        f"Last successful run of {actor_name}: {run_url}, "
        f"finished {run_info['finishedAt']}, "
        f"took {run_info['stats']['runTimeSecs']}s"
    )
    dataset = last_run.dataset()
    return list(dataset.iterate_items())
