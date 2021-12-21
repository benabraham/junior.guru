import os
from datetime import date

from fiobank import FioBank

from juniorguru.lib.timer import measure
from juniorguru.lib import google_sheets, loggers
from juniorguru.models import Transaction


logger = loggers.get('transactions')


FROM_DATE = date(2020, 1, 1)
FIOBANK_API_KEY = os.getenv('FIOBANK_API_KEY')
SIDELINE_JOBS = ['15']
CATEGORIES = [
    lambda t: 'memberships' if t['variable_symbol'] == '21' else None,
    lambda t: 'salary' if 'výplata' in t['message'] else None,
    lambda t: 'sideline' if t['variable_symbol'] in SIDELINE_JOBS else None,
    lambda t: 'lawyer' if 'ADVOKATKA' in t['message'] else None,
    lambda t: 'discord' if 'DISCORD' in t['message'] and t['amount'] < 0 else None,
    lambda t: 'partnerships' if 'RED HAT' in t['message'] and t['amount'] >= 8000 else None,
    lambda t: 'tax' if ('ČSSZ' in t['message'] or 'PSSZ' in t['message'] or 'MSSZ' in t['message']) else None,
    lambda t: 'tax' if 'VZP' in t['message'] else None,
    lambda t: 'marketing' if 'PrintAll' in t['message'] and t['amount'] < 0 else None,
    lambda t: 'donations' if 'GITHUB SPONSORS' in t['message'] and t['amount'] > 0 else None,
    lambda t: 'memberships' if 'STRIPE' in t['message'] and t['amount'] > 0 else None,
    lambda t: 'donations' if 'PAYPAL' in t['message'] and t['amount'] > 0 else None,
    lambda t: 'donations' if not t['variable_symbol'] and t['amount'] > 0 else None,
    lambda t: 'donations' if t['variable_symbol'] == '444222' and t['amount'] > 0 else None,
    lambda t: 'partnerships' if t['variable_symbol'] and t['amount'] >= 8000 else None,
    lambda t: 'jobs' if t['variable_symbol'] and t['amount'] > 0 else None,
    lambda t: 'donations' if t['amount'] > 0 else 'overheads',
]
DOC_KEY = '1TO5Yzk0-4V_RzRK5Jr9I_pF5knZsEZrNn2HKTXrHgls'


@measure('transactions')
def main():
    logger.info('Preparing database')
    Transaction.drop_table()
    Transaction.create_table()

    logger.info('Reading data from the bank account')
    client = FioBank(token=FIOBANK_API_KEY)
    from_date = FROM_DATE.strftime('%Y-%m-%d')
    to_date = date.today().strftime('%Y-%m-%d')
    transactions = client.period(from_date=from_date, to_date=to_date)

    db_records = []
    doc_records = []

    for transaction in transactions:
        logger.debug(f"{transaction['date']} {transaction['amount']}")

        if transaction['currency'].upper() != 'CZK':
            raise ValueError(f"Unexpected currency: {transaction['currency']}")

        message = ', '.join(filter(None, [
            transaction.get('comment'),
            transaction.get('user_identification'),
            transaction.get('recipient_message'),
        ]))
        category = get_category(dict(message=message, **transaction))

        db_records.append(dict(happened_on=transaction['date'],
                               category=category,
                               amount=transaction['amount']))
        doc_records.append({
            'Date': transaction['date'].strftime('%Y-%m-%d'),
            'Category': category,
            'Amount': transaction['amount'],
            'Message': message,
            'Variable Symbol': transaction['variable_symbol'],
        })

    logger.info('Saving essential data to the database')
    for db_record in db_records:
        Transaction.create(**db_record)

    logger.info('Uploading verbose data to a private Google Sheet for manual audit of possible mistakes')
    google_sheets.upload(google_sheets.get(DOC_KEY, 'transactions'), doc_records)


def get_category(transaction):
    for category_fn in CATEGORIES:
        category = category_fn(transaction)
        if category:
            return category
    raise ValueError('Could not categorize transaction')


if __name__ == '__main__':
    main()
