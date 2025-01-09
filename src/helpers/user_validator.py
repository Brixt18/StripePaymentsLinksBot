import csv
import logging
from os import getenv

from conts import PATH


class UserValidator:
    def __init__(self):
        self._path = PATH

        self.whitelisted_users = self._get_whitelisted_users()
        logging.debug(f"Whitelisted users: {self.whitelisted_users}", extra={
                      'function': 'UserValidator.__init__'})

        self.blacklisted_users = self._get_blacklisted_users()
        logging.debug(f"Blacklisted users: {self.blacklisted_users}", extra={
                      'function': 'UserValidator.__init__'})

        self.only_whitelisted = int(getenv("ONLY_WHITELISTED", 0))
        logging.debug(f"Only whitelisted: {self.only_whitelisted}", extra={
                      'function': 'UserValidator.__init__'})

    def _get_whitelisted_users(self):
        try:
            with open(f'{self._path}/config/whitelist.csv', mode='r') as file:
                csv_reader = csv.DictReader(file)
                return {row['user_id'] for row in csv_reader}

        except FileNotFoundError:
            logging.error("Whitelist file not found.", extra={
                          'function': 'UserValidator._get_whitelisted_users'})

        return set()

    def _get_blacklisted_users(self):
        try:
            with open(f'{self._path}/config/blacklist.csv', mode='r') as file:
                csv_reader = csv.DictReader(file)
                return {row['user_id'] for row in csv_reader}

        except FileNotFoundError:
            logging.error("Blacklist file not found.", extra={
                          'function': 'UserValidator._get_whitelisted_users'})

        return set()

    def user_can_access(self, user_id: str) -> bool:
        """
        Check if a user can access the system.
        """
        if self.only_whitelisted:
            logging.debug(f"Checking if user {user_id} is whitelisted.", extra={
                          'function': 'UserValidator.user_can_access'})
            return str(user_id) in self.whitelisted_users

        logging.debug(f"Checking if user {user_id} is not blacklisted.", extra={
                      'function': 'UserValidator.user_can_access'})
        return str(user_id) not in self.blacklisted_users
