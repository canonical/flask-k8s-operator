# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Synchronized secret data management across all units in the flask application."""

import json
import logging
import secrets
import typing

from ops.charm import CharmBase
from ops.framework import Object
from ops.jujuversion import JujuVersion
from ops.model import Relation, RelationDataContent

if typing.TYPE_CHECKING:
    JSON: typing.TypeAlias = typing.Union[
        typing.Dict[str, "JSON"], typing.List["JSON"], str, int, float, bool, None
    ]
    from charm import FlaskCharm

logger = logging.getLogger(__name__)


class SecretsNotSupported(RuntimeError):
    pass


class SecretStorage(Object):
    """Synchronized secret data management across all units in the same application.

    Attrs:
        is_initialized: Check if the secret storage has been initialized. It is an error to
            read or write before the secret storage is initialized.
    """

    def __init__(
        self,
        charm: CharmBase,
        on_change=typing.Callable[["SecretStorage"], None],
        peer_integration_name="secret-storage",
    ):
        """Initialize the SecretStorage instance.

        Args:
            charm: The charm application that owns this secret storage.
            on_change: A callback function to be invoked when there are changes in the secret
                storage. It accepts the secret storage object as its sole argument.
            peer_integration_name: The name of the peer integration. Defaults to "secret-storage".

        Raises:
            SecretsNotSupported: If the current Juju environment does not support secrets.
        """
        super().__init__(charm, peer_integration_name)
        if not JujuVersion.from_environ().has_secrets:
            raise SecretsNotSupported()
        self._charm = charm
        self._peer_integration = peer_integration_name
        self._on_change = on_change
        self._charm.framework.observe(
            self._charm.on[self._peer_integration].relation_changed, self._on_relation_changed
        )
        self._charm.framework.observe(
            self._charm.on[self._peer_integration].relation_created, self._on_relation_changed
        )
        self._charm.framework.observe(self._charm.on.secret_remove, self._on_secret_remove)

    def _on_secret_remove(self, event):
        """Event handler for cleaning up unused secret revisions created by the secret storage.

        Args:
            event: The secret-remove event triggering this handler.
        """
        if not self.is_initialized:
            return
        secret = event.secret
        relation_data = self._get_relation_data()
        secret_id = relation_data.get("id")
        if secret.id == secret_id:
            # https://bugs.launchpad.net/juju/+bug/2023364
            # juju secret-remove event fired on tracking secret revision
            # disable removal of old revisions temporarily
            # secret.remove_revision(event.revision)
            pass

    def _get_relation(self) -> typing.Optional[Relation]:
        """
        Retrieve the relation object associated with this secret storage.

        Returns:
            The relation object associated with the peer integration in the charm model, or None
            if the relation hasn't been created yet.
        """
        return self._charm.model.get_relation(self._peer_integration)

    def _get_relation_data(self) -> RelationDataContent:
        """
        Retrieve the application relation data of the associated relation.

        Raises:
            RuntimeError: If the function is called before the relation is created.

        Returns:
            The application relation data of the associated relation.
        """
        relation = self._get_relation()
        if relation is None:
            raise RuntimeError("secret store accesses relation data before relation is created")
        return relation.data[self._charm.app]

    def _get_secret_data(self) -> typing.Tuple[int, typing.Dict[str, "JSON"]]:
        """Retrieve the secret revision and secret data stored by secret storage in juju secret.

        Returns:
            A tuple containing the secret revision and the secret data.
        """
        self._check_initialized()
        relation_data = self._get_relation_data()
        revision = int(relation_data["revision"])
        secret_id = relation_data["id"]
        secret = self._charm.model.get_secret(id=secret_id)
        return revision, self._decode_secret_content(secret.get_content(refresh=True))

    def _set_secret_data(self, data: typing.Dict[str, "JSON"]):
        """Store the secret data in the Juju secret system.

        Args:
            data: A dictionary containing key-value pairs representing the secret data.
        """
        self._check_initialized()
        relation_data = self._get_relation_data()
        secret_id = relation_data["id"]
        secret = self._charm.model.get_secret(id=secret_id)
        secret.set_content(self._encode_secret_content(data))
        relation_data["revision"] = str(int(relation_data["revision"]) + 1)

    def _initialize(self):
        """Initialize the secret storage in the Juju environment.

        This method creates a new secret and sets the initial revision and id in relation data.
        """
        relation_data = self._get_relation_data()
        secret = self._charm.app.add_secret(content=self._encode_secret_content({}))
        relation_data.update({"revision": "1", "id": secret.id})

    @property
    def is_initialized(self) -> bool:
        """Check if the secret storage has been initialized in the associated relation.

        It is an error to read or write before the secret storage is initialized.

        Returns:
            True if the secret storage is initialized (both revision and id exist).
        """
        relation = self._get_relation()
        if relation is None:
            return False
        relation_data = self._get_relation_data()
        return bool(relation_data.get("revision") and relation_data.get("id"))

    def _check_leader(self):
        """Validate if the current operating unit is the leader unit.

        Raises:
            RuntimeError: If the current operating unit is not the leader unit.
        """
        if not self._charm.unit.is_leader():
            raise RuntimeError("only leader can update secret storage")

    def _check_initialized(self):
        """Validate if the current operating unit is the leader unit.

        Raises:
            RuntimeError: If the current operating unit is not the leader unit.
        """
        if not self.is_initialized:
            raise RuntimeError("secret store attempt to access values before initialization")

    def _on_relation_changed(self, _):
        """Handles the relation-changed event in Juju.

        The method takes appropriate action based on the initialization status of the secret
        storage, and invokes the 'on_change' callback function when there are changes in the
        secret storage.
        """
        logging.info("relation-changed event in secret storage")
        if not self.is_initialized:
            if self._charm.unit.is_leader():
                self._initialize()
            return
        revision, secret_data = self._get_secret_data()
        if revision == 1:
            return
        self._on_change(self)

    @staticmethod
    def _encode_secret_content(data: typing.Dict[str, "JSON"]) -> typing.Dict[str, str]:
        """Encode the secret data into a format acceptable by the juju secret system.

        Args:
            data: The secret data as a dictionary.

        Returns:
            The encoded secret data as a dictionary.
        """
        return {"data": json.dumps(data, sort_keys=True)}

    @staticmethod
    def _decode_secret_content(content: typing.Dict[str, str]) -> typing.Dict[str, "JSON"]:
        """Decode the secret data from the format used by the Juju secret system.

        Args:
            content: The encoded secret data as a dictionary from juju secret.

        Returns:
            The decoded secret data as a dictionary.
        """
        return json.loads(content["data"])

    def put(self, key: str, value: "JSON"):
        """Add or update a key-value pair in the secret storage.

        If changes are made, the 'on_change' callback is invoked on all units.

        Args:
            key: The key of the item.
            value: The value to associate with the key.
        """
        self._check_leader()
        self._check_initialized()
        _, secret_data = self._get_secret_data()
        try:
            current_value = secret_data[key]
            if current_value == value:
                return
        except KeyError:
            pass
        secret_data[key] = value
        self._set_secret_data(secret_data)

    def delete(self, key: str):
        """Remove a key from the secret storage.
        It is not considered an error if the key does not exist. If changes are made,
        the 'on_change' callback is invoked on all units.

        Args:
            key (str): The key to be removed.
        """
        self._check_leader()
        self._check_initialized()
        _, secret_data = self._get_secret_data()
        if key not in secret_data:
            return
        del secret_data[key]
        self._set_secret_data(data=secret_data)

    def get_item(self, key: str) -> "JSON":
        """Retrieve the value associated with a key from the secret storage.

        Args:
            key: The key of the item to be retrieved.

        Returns:
            The value associated with the key.

        Raises:
            KeyError: if the key does not exist.
        """
        self._check_initialized()
        _, secret_data = self._get_secret_data()
        return secret_data[key]

    def get_all(self) -> typing.Dict[str, "JSON"]:
        """Retrieves all data from the secret storage.

        Returns:
            A dictionary containing all the data in the secret storage.
        """
        self._check_initialized()
        _, secret_data = self._get_secret_data()
        return secret_data


class FlaskSecretStorage:
    # bandit thinks this is a password
    _FLASK_SECRET_KEY_STORAGE_KEY = "FLASK_SECRET_KEY"  # nosec

    def __init__(self, charm: "FlaskCharm"):
        self._secret_storage = SecretStorage(charm=charm, on_change=lambda _: None)

    def ready(self) -> bool:
        """Check if the FlaskSecretStorage is ready with all default secrets generated.

        Returns:
            True, if the FlaskSecretStorage is ready.
        """
        if not self._secret_storage.is_initialized:
            return False
        try:
            self._secret_storage.get_item(self._FLASK_SECRET_KEY_STORAGE_KEY)
        except KeyError:
            self._secret_storage.put(self._FLASK_SECRET_KEY_STORAGE_KEY, secrets.token_urlsafe(32))
            return False

    def get_secret_key(self) -> str:
        """Return the generated default Flask secret key.

        Returns:
            generated Flask secret key

        Raises:
            RuntimeError: if this method is called before flask secret storage is ready.
        """
        if not self.ready():
            raise RuntimeError("flask secret storage is not ready")
        return self._secret_storage.get_item(self._FLASK_SECRET_KEY_STORAGE_KEY)
