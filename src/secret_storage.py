# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the SecretStorage for managing the persistent secret storage for the Flask charm."""

import secrets
import typing

import ops


class SecretStorage(ops.Object):
    """A class that manages secret keys required by the FlaskCharm.

    Attrs:
        is_initialized: True if the SecretStorage has been initialized.
    """

    # bandit think this is a password
    _FLASK_SECRET_KEY_KEY = "flask_secret_key"  # nosec
    _PEER_RELATION_NAME = "secret-storage"

    def __init__(self, charm: ops.CharmBase):
        """Initialize the SecretStorage with a given FlaskCharm object.

        Args:
            charm (FlaskCharm): The FlaskCharm object that uses the SecretStorage.
        """
        super().__init__(parent=charm, key=self._PEER_RELATION_NAME)
        self._charm = charm
        charm.framework.observe(
            self._charm.on[self._PEER_RELATION_NAME].relation_created,
            self._on_secret_storage_relation_created,
        )

    def _on_secret_storage_relation_created(self, event: ops.RelationEvent) -> None:
        """Handle the event when a new peer relation is created.

        Generates a new secret key and stores it within the relation's data.

        Args:
            event: The event that triggered this handler.
        """
        relation_data = event.relation.data[self._charm.app]
        if self._charm.unit.is_leader() and not relation_data.get(self._FLASK_SECRET_KEY_KEY):
            secret_key = secrets.token_urlsafe(32)
            relation_data[self._FLASK_SECRET_KEY_KEY] = secret_key

    @property
    def is_initialized(self) -> bool:
        """Check if the SecretStorage has been initialized.

        It's an error to read or write the secret storage before initialization.

        Returns:
            True if SecretStorage is initialized, False otherwise.
        """
        relation = self._charm.model.get_relation(self._PEER_RELATION_NAME)
        if relation is None:
            return False
        relation_data = relation.data[self._charm.app]
        return relation_data.get(self._FLASK_SECRET_KEY_KEY) is not None

    def _get_relation_data(self) -> ops.RelationDataContent:
        """Retrieve the relation data associated with the FlaskCharm object.

        Returns:
            RelationDataContent: The data of the relation associated with the FlaskCharm app.

        Raises:
            RuntimeError: If SecretStorage is not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError("SecretStorage is not initialized")
        relation = typing.cast(
            ops.Relation, self._charm.model.get_relation(self._PEER_RELATION_NAME)
        )
        data = relation.data[self._charm.app]
        return data

    def get_flask_secret_key(self) -> str:
        """Retrieve the Flask secret key from the peer relation data.

        Returns:
            The Flask secret key.
        """
        data = self._get_relation_data()
        return data[self._FLASK_SECRET_KEY_KEY]

    def reset_flask_secret_key(self) -> None:
        """Generate a new Flask secret key and store it within the peer relation data."""
        data = self._get_relation_data()
        data[self._FLASK_SECRET_KEY_KEY] = secrets.token_urlsafe(32)
