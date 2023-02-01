import asyncio
from datetime import date, timedelta
from pathlib import Path

from discord import Color, Embed, File

from juniorguru.cli.sync import main as cli
from juniorguru.lib import loggers
from juniorguru.lib.club import BOT_CHANNEL  # INTRO_CHANNEL
from juniorguru.lib.club import DISCORD_MUTATIONS_ENABLED  # JOBS_CHANNEL,
from juniorguru.lib.club import is_message_over_period_ago, run_discord_task
from juniorguru.models.base import db
from juniorguru.models.club import ClubMessage
from juniorguru.models.partner import Partner


MESSAGE_EMOJI = '👋'

BOT_REACTIONS = ['👋', '👍', '💕', '💰']

COMPANIES_INTRO_LAUNCH_ON = date(2022, 4, 1)

IMAGES_DIR = Path(__file__).parent.parent / 'images'

INTRO_CHANNEL = BOT_CHANNEL  # FIXME


logger = loggers.from_path(__file__)


@cli.sync_command(dependencies=['club-content', 'partners', 'roles'])
def main():
    run_discord_task('juniorguru.sync.partners_intro.discord_task')


@db.connection_context()
async def discord_task(client):
    last_message = ClubMessage.last_bot_message(INTRO_CHANNEL, MESSAGE_EMOJI)
    if is_message_over_period_ago(last_message, timedelta(weeks=1)):
        logger.info('Last company intro message is more than one week old!')

        partners = [company for company in Partner.active_listing()
                     if doesnt_have_intro(company)]
        if partners:
            logger.debug(f'Choosing from {len(partners)} partners to announce')
            company = sorted(partners, key=sort_key)[0]
            partnership = company.active_partnership()

            logger.debug(f'Decided to announce {company!r}')
            if DISCORD_MUTATIONS_ENABLED:
                channel = await client.fetch_channel(INTRO_CHANNEL)
                content = (
                    f"{MESSAGE_EMOJI} "
                    f"Kamarádi z {company_name_formatted(company.name)} se rozhodli podpořit klub a jsou tady s námi! "
                    f"Mají roli <@&{company.role_id}>."
                )
                if partnership.starts_on < COMPANIES_INTRO_LAUNCH_ON and (date.today() - partnership.starts_on).days > 30:
                    content += (
                        ' 🐣 Sice to píšu jako novinku, ale ve skutečnosti klub podporují už od '
                        f'{partnership.starts_on.day}.{partnership.starts_on.month}.{partnership.starts_on.year}. '
                        'Jenže tehdy jsem bylo malé kuřátko, které ještě neumělo vítat firmy.'
                    )

                embed_description_lines = [
                    f"ℹ️ Víc o firmě najdeš na [jejich webu]({company.url})",
                    "🛡 Mají logo na [stránce klubu](https://junior.guru/club/)",
                ]
                # if company.is_sponsoring_handbook:
                #     embed_description_lines.append('📖 Mají logo na [příručce pro juniory](https://junior.guru/handbook/)')
                # if company.job_slots_count:
                #     embed_description_lines.append(f'🧑‍💻 Mají inzeráty v <#{JOBS_CHANNEL}> a [na webu](https://junior.guru/jobs/)')
                if company.student_role_id:
                    embed_description_lines.append(f'🧑‍🎓 Posílají sem své studenty: <@&{company.student_role_id}>')
                embed_description_lines += [
                    "💕 Chtějí pomáhat juniorům!",
                    '💰 Financují práci na [příručce pro juniory](https://junior.guru/handbook/)',
                    '\nJak přesně funguje spolupráce s firmami? Mrkni do [FAQ](https://junior.guru/faq/#firmy)',
                ]

                embed = Embed(title=company.name, color=Color.dark_grey(),
                              description='\n'.join(embed_description_lines))
                embed.set_thumbnail(url=f"attachment://{Path(company.poster_path).name}")
                file = File(IMAGES_DIR / company.poster_path)

                message = await channel.send(content=content, embed=embed, file=file)
                await asyncio.gather(*[message.add_reaction(emoji) for emoji in BOT_REACTIONS])
            else:
                logger.warning('Discord mutations not enabled')
        else:
            logger.info('No partners to announce')
    else:
        logger.info('Last company intro message is less than one week old')


def company_name_formatted(company_name):
    return f'**{company_name}**'


def doesnt_have_intro(company):
    message = ClubMessage.last_bot_message(INTRO_CHANNEL, MESSAGE_EMOJI,
                                           company_name_formatted(company.name))
    return is_message_over_period_ago(message, timedelta(days=365))


def sort_key(company, today=None):
    today = today or date.today()
    partnership = company.active_partnership()
    expires_on = (partnership.expires_on or date(3000, 1, 1))
    expires_in_days = (expires_on - today).days
    started_days_ago = (today - partnership.starts_on).days
    return (expires_in_days if expires_in_days <= 30 else 1000,
            started_days_ago,
            company.name)
