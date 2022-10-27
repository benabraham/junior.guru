from pathlib import Path

from strictyaml import Datetime, Map, Seq, Str, Url, load

from juniorguru.lib import loggers
from juniorguru.cli.sync import subcommands as cli
from juniorguru.models.base import db
from juniorguru.models.story import Story


YAML_PATH = Path('juniorguru/data/stories.yml')

YAML_SCHEMA = Seq(
    Map({
        'url': Url(),
        'date': Datetime(),
        'title': Str(),
        'image_path': Str(),
        'tags': Seq(Str()),
    })
)


logger = loggers.get(__name__)


@cli.command()
@db.connection_context()
def main():
    Story.drop_table()
    Story.create_table()
    for yaml_record in load(YAML_PATH.read_text(), YAML_SCHEMA):
        record = yaml_record.data
        logger.info(record['title'])
        Story.create(**record)
