import getpass
import json
import sys

import gkeepapi
import keyring

DO_REAL_SYNC = False  # debugging tool, so i don't have to wait while it pulls down again.


class ChoreMinder:
    def __init__(self):
        self.keep = get_api()

        self.sync_data(from_file=True)

        self.all_labels = self.get_labels()
        self.unlabeled = self.get_unlabeled()

    def main(self):
        raise hell  # force to debugger

    def sync_data(self, from_file=False):
        print('Syncing...')

        if from_file:
            try:
                with open('cache.json', 'r') as f:
                    state = json.load(f)
                    self.keep.restore(state)
            except FileNotFoundError:
                print('no cache to resume from')
                pass

        if DO_REAL_SYNC:
            self.keep.sync()

        with open('cache.json', 'w') as f:
            json.dump(self.keep.dump(), f)

        print('Synced')

    def get_labels(self):
        labels = {}
        for label in self.keep.labels():
            labels[label.name] = label

        return labels

    def get_unlabeled(self):
        unlabeled = []
        for note in self.keep.all():
            if note.deleted or note.trashed:
                continue

            no_labels = len(note.labels) == 0
            is_note = note.type.name == 'Note'  # excludes lists

            if no_labels and is_note:
                unlabeled.append(note)

        unlabeled.sort(key=lambda x: x.timestamps.updated, reverse=True)

        return unlabeled


def get_api():
    # username = input('google email?')  # TODO: change back to asking every time
    username = 'tom@tomlat.com'

    # Initialize the client
    keep = gkeepapi.Keep()

    token = keyring.get_password("google-keep-token", username)
    logged_in = False

    # Use an existing master token if one exists
    if token:
        print("Authenticating with token")
        try:
            keep.resume(username, token, sync=False)
            logged_in = True
            print("Success")
        except gkeepapi.exception.LoginException:
            print("Invalid token")

    # Otherwise, prompt for credentials and login
    if not logged_in:
        password = getpass.getpass()
        try:
            keep.login(username, password, sync=False)
            logged_in = True
            del password
            token = keep.getMasterToken()
            keyring.set_password("google-keep-token", username, token)
            print("Success")
        except gkeepapi.exception.LoginException as e:
            print(e)

    # Abort if authentication failed
    if not logged_in:
        print("Failed to authenticate")
        sys.exit(1)

    return keep


if __name__ == '__main__':
    cm = ChoreMinder()
    cm.main()
