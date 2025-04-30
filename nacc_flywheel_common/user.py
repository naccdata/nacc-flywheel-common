"""Defines a repository for user objects."""

import logging
from typing import List, Optional

from flywheel import Client, User
from flywheel.rest import ApiException
from pydantic import BaseModel

log = logging.getLogger(__name__)


class UserModel(BaseModel):
    """The data model for user information."""

    firstname: str
    lastname: str
    id: str
    email: str


class UserRepository:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.__user_map = {}

    def get(self, user_id: str) -> Optional[User]:
        """Gets the user with the ID if it is exists.

        Args:
          user_id: the user ID
        Returns:
          the user with the ID if one exists. None, otherwise
        """
        if not self.__user_map:
            self.__get_users()

        return self.__user_map.get(user_id)

    def __get_users(self) -> None:
        """Pulls the users from Flywheel and creates a dictionary on user
        ID."""
        users = self.client.users()
        self.__user_map = {
            user.id: user
            for user in users
            if not user.disabled and "@flywheel.io" not in user.id
        }

    def add(self, user_model: UserModel) -> User:
        """Adds a user for the user model.

        Args:
          user_model: the user information
        Returns:
          the corresponding user object
        """
        try:
            user = self.get(user_model.id)
        except ApiException:
            log.info("user %s not found", user_model.id)

        if not user:
            log.info("Creating user with ID %s", user_model.id)
            self.client.add_user(
                User(
                    id=user_model.id,
                    firstname=user_model.firstname,
                    lastname=user_model.lastname,
                    email=user_model.id,
                )
            )

        self.client.modify_user(user_model.id, {"email": user_model.email})
        user = self.client.get_user(user_model.id)
        self.__user_map[user.id] = user

        return user

    def add_list(self, user_list: List[UserModel]) -> List[User]:
        """Adds users for the list of user model objects and returns the Users.

        Args:
          user_list: the list of user model objects
        Returns:
          the list of corresponding users
        """
        return [self.add(user_model) for user_model in user_list]

    def list(self, id_list: Optional[List[str]] = None) -> List[User]:
        """Returns the list of users for the IDs.

        Args:
          id_list: the list of user IDs
        Returns:
          the list of users for the IDs
        """
        if not self.__user_map:
            self.__get_users()

        if not id_list:
            return list(self.__user_map.values())

        return [
            self.__user_map.get(user_id)
            for user_id in id_list
            if user_id in self.__user_map
        ]
