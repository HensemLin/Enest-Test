import logging
import random
import string
import time

from passlib.context import CryptContext

api_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash(api_key: str):
    """
    Hashes the provided API key.

    Args:
        api_key (str): The API key to be hashed.

    Returns:
        str: The hashed API key.

    Raises:
        Exception: If an error occurs during the hashing process.
    """
    try:
        return api_context.hash(api_key)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e


def generate_api_key():
    """
    Generates a random API key.

    Returns:
        str: The randomly generated API key.

    Raises:
        Exception: If an error occurs during the key generation process.
    """
    try:
        api_key = "".join(random.choices(string.ascii_letters + string.digits, k=30))
        return api_key

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e


def verify_api_key(plain_api_key, hashed_api_key):
    """
    Verifies a plain API key against its hashed counterpart.

    Args:
        plain_api_key (str): The plain API key to be verified.
        hashed_api_key (str): The hashed API key to be checked against.

    Returns:
        bool: True if the verification is successful, False otherwise.

    Raises:
        Exception: If an error occurs during the verification process.
    """
    try:
        return api_context.verify(plain_api_key, hashed_api_key)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False


def generate_unique_id():
    """
    Generates a unique ID based on timestamp and random characters.

    Returns:
        str: The generated unique ID.

    Raises:
        Exception: If an error occurs during the ID generation process.
    """
    try:
        timestamp = int(time.time())
        random_string = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        unique_id = f"{timestamp}_{random_string}"
        return unique_id

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e
