import getpass
import json

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


def main():
    keep = gkeepapi.Keep()
    auth(keep)
    notes = keep.all()
    print(notes[0])


if __name__ == "__main__":
    main()
