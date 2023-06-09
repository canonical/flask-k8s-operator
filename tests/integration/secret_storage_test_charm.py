import json
import pathlib

from ops.framework import EventBase

from any_charm_base import AnyCharmBase
from secret_storage import SecretStorage


class AnyCharm(AnyCharmBase):
    _CHANGE_HISTORY_PATH = pathlib.Path("/tmp/change-history.json")
    _EVENT_HISTORY_PATH = pathlib.Path("/tmp/event-history.json")
    _EVENTS = (
        'install',
        'start',
        'stop',
        'remove',
        'update_status',
        'config_changed',
        'upgrade_charm',
        'pre_series_upgrade',
        'post_series_upgrade',
        'leader_elected',
        'leader_settings_changed',
        'collect_metrics',
        'secret_changed',
        'secret_expired',
        'secret_rotate',
        'secret_remove',
        'peer_any_relation_created',
        'peer_any_relation_joined',
        'peer_any_relation_changed',
        'peer_any_relation_departed',
        'peer_any_relation_broken',
    )

    def __init__(self, *args):
        super().__init__(*args)
        self.secret_storage = SecretStorage(
            charm=self,
            on_change=self._on_secret_storage_change,
            peer_integration_name="peer-any"
        )
        if self.secret_storage.is_initialized:
            try:
                self.secret_storage.get_item("foo")
            except KeyError:
                pass
        for event in self._EVENTS:
            self.framework.observe(getattr(self.on, event), self._on_everything)

    def _append_json(self, json_file: pathlib.Path, data):
        if not json_file.exists():
            json.dump([data], json_file.open("w+"))
            return
        history = json.load(json_file.open())
        history.append(data)
        json.dump(history, json_file.open("w"))

    def _on_secret_storage_change(self, secret_storage):
        self._append_json(self._CHANGE_HISTORY_PATH, secret_storage.get_all())

    def get_change_history(self):
        if self._CHANGE_HISTORY_PATH.exists():
            return json.load(self._CHANGE_HISTORY_PATH.open())
        return []

    def _on_everything(self, event: EventBase):
        record = {
            "event": event.__class__.__name__,
            "is_initialized": self.secret_storage.is_initialized
        }
        self._append_json(self._EVENT_HISTORY_PATH, record)

    def get_event_history(self):
        if self._EVENT_HISTORY_PATH.exists():
            return json.load(self._EVENT_HISTORY_PATH.open())
        return []

    def get(self, key):
        return self.secret_storage.get_item(key)

    def get_all(self):
        return self.secret_storage.get_all()

    def put(self, key, value):
        self.secret_storage.put(key, value)

    def delete(self, key):
        self.secret_storage.delete(key)
