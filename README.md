# bot_solaris

Telegram bot on `aiogram` that:

- shows a menu of services and directions;
- gives short first-line information for each item;
- collects name and phone when the user wants to continue;
- finds an existing lead in Bitrix24 by phone number;
- creates a lead if one does not exist yet;
- appends a new request context to an existing lead if it already exists;
- writes what the user selected into `COMMENTS` for the manager;
- does not create product rows for the lead.

## Current flow

1. `/start`
2. The user chooses `Activities`, `Rent`, or `Event`.
3. The bot shows short information.
4. After `Leave a request`, the bot collects name and phone.
5. Bitrix24 receives a new or existing lead update with the request context in `COMMENTS`.

## Product direction

The bot is meant to reduce the managers' first-line workload:

- answer basic questions that users would otherwise search for on the website;
- guide the user through menu buttons before a human joins;
- collect a readable summary of what the client was interested in;
- pass the manager a request description and selection path, not a linked product.

Target examples:

- `Corporate event` -> group size -> selected activities -> manager follow-up.
- `Karting` -> opening hours / admission rules / booking -> manager follow-up.

## Setup

1. Create `.env` from `.env.example`.
2. Set:
   - `BOT_TOKEN`
   - `BITRIX_WEBHOOK_URL`
   - optionally `BITRIX_ASSIGNED_BY_ID`
3. Install dependencies:

```bash
pip install -e .
```

4. Run:

```bash
python main.py
```

## Bitrix24 logic

1. `crm.duplicate.findbycomm` searches for a lead by phone.
2. If nothing is found, `crm.lead.list` is used as a fallback.
3. If there is no lead, the bot creates one via `crm.lead.add`.
4. If a lead exists, the bot appends the new request context via `crm.lead.update`.
5. Category, interest, selection path, and extra user notes are stored in `COMMENTS`.
6. No product rows are attached to the lead.
