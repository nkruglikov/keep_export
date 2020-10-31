import datetime
import getpass
import json
from collections import defaultdict

import gkeepapi
import keyring


def auth(keep):
    creds = keyring.get_password("keep_sync", "creds")
    if creds is None:
        email = input("email: ")
        password = getpass.getpass("password: ")
        keep.login(email, password)

        token = keep.getMasterToken()
        creds = json.dumps({"email": email, "token": token})
        keyring.set_password("keep_sync", "creds", creds)
    else:
        creds = json.loads(creds)
        email = creds["email"]
        token = creds["token"]
        keep.resume(email, token)


def obsidian_timestamp(ts):
    date = ts.date().isoformat()
    obs_ts = ts.strftime("%d.%m.%y %H:%M")
    return f"[[Dates/{date}|{obs_ts}]]"


def get_created(note):
    created = note.timestamps.created
    created = created.replace(tzinfo=datetime.timezone.utc).astimezone()
    return created


def render_note(note):
    created = get_created(note)
    created = obsidian_timestamp(created)
    title = note.title
    text = note.text

    return f"{created} {title}\n{text}"


def render_group(group):
    first_created = get_created(group[0])
    first_created = obsidian_timestamp(first_created)
    header = (f"created: {first_created}\n"
              f"tags: #keep\n\n"
              f"---\n\n")
    body = [render_note(note) for note in group]
    return header + "\n\n---\n\n".join(body)


def get_daily_groups(keep):
    notes = keep.all()
    groups = defaultdict(list)
    for note in reversed(notes):
        if note.pinned or note.archived or note.trashed:
            continue
        created = get_created(note)
        date = created.date().isoformat()
        groups[date].append(note)
    groups = [(date, group) for date, group in groups.items()]
    groups.sort()
    return groups


def main():
    keep = gkeepapi.Keep()
    auth(keep)
    exported = keep.findLabel("exported")

    groups = get_daily_groups(keep)
    for date, group in groups:
        print(f"Processing {date}...")
        title = f"Keep {date}.md"
        content = render_group(group)
        with open(title, "w") as out:
            out.write(content)
        for note in group:
            note.labels.add(exported)
            note.archived = True
    keep.sync()


if __name__ == "__main__":
    main()
