import datetime
import logging

import pytz
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..common import utils
from .models import ApiKey
from .schemas import ApiKeyResponse


async def create_api_key(db: Session) -> ApiKeyResponse:
    """
    Create a new API key for the company.

    Args:
        db (Session): The database session.

    Returns:
        ApiKeyResponse: The created API key data.

    Raises:
        HTTPException: If any unexpected error occurs.
    """
    try:
        """Generate a new API key and its ID"""
        api_key = utils.generate_api_key()
        api_key_id = utils.generate_unique_id()

        """Add the new API key object to the database"""
        new_hashed_api_key = ApiKey(apiKey_id=api_key_id, apiKey=utils.hash(api_key))

        db.add(new_hashed_api_key)

        """Commit the changes to the database"""
        db.commit()

        return ApiKeyResponse(
            id=api_key_id,
            apiKey=api_key,
            created_at=datetime.datetime.now(
                pytz.timezone("Asia/Kuala_Lumpur")
            ).strftime("%Y-%m-%dT%H:%M:%S"),
        )

    except SQLAlchemyError as sqla_error:
        logging.error("SQLAlchemy error occurred: {}".format(str(sqla_error)))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def get_all_api_keys(db: Session) -> list[ApiKey]:
    """
    Get all API keys for the given company.

    Args:
        db (Session): The database session.

    Returns:
        list[ApiKey]: List of all API keys.

    Raises:
        HTTPException: If no API keys are found for the company
                        or if any unexpected error occurs.
    """
    try:
        """Get all API keys for the given company from the database"""
        api_keys = db.query(ApiKey).all()

        """If no API keys are found, raise a 404 Not Found error"""
        if not api_keys:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No API key(s) found"
            )

        """Set the 'id' attribute of each API key to 'apiKey_id'"""
        for api_key in api_keys:
            api_key.id = api_key.apiKey_id

        return api_keys

    except SQLAlchemyError as sqla_error:
        logging.error("SQLAlchemy error occurred: {}".format(str(sqla_error)))
        db.rollback()  # Rollback the transaction in case of an SQLAlchemy error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def get_api_key_by_id(id: str, db: Session) -> ApiKey:
    """
    Get a specific API key for the given company.

    Args:
        id (str): The ID of the API key to retrieve.
        db (Session): The database session.

    Returns:
        ApiKey: The requested API key.

    Raises:
        HTTPException: If the specified API key is not found, a 404 Not Found Error is raised.
        HTTPException: If any other unexpected error occurs, a 500 Internal Server Error is raised.
    """
    try:
        api_key = (
            db.query(ApiKey)
            .filter(
                ApiKey.apiKey_id == id,
            )
            .first()
        )

        """If the API key is not found, raise a 404 Not Found error"""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No API key(s) found"
            )

        """Set the 'id' attribute of the API key to 'apiKey_id'"""
        api_key.id = api_key.apiKey_id

        return api_key

    except SQLAlchemyError as sqla_error:
        logging.error("SQLAlchemy error occurred: {}".format(str(sqla_error)))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def delete_api_key(id: str, db: Session) -> None:
    """
    Deletes a specific API key by ID.

    Args:
        id (str): The ID of the API key to delete.
        db (Session): The database session dependency.

    Raises:
        HTTPException: If any error happened in the sqlalchemy
        HTTPException: If the API key with the specified ID does not exist, a 404 Not Found error is raised.
        HTTPException: If any other unexpected error occurs, a 500 Internal Server Error is raised.
    """
    try:
        """Query the API key by ID"""
        api_key_query = db.query(ApiKey).filter(
            ApiKey.apiKey_id == id,
        )

        api_key = api_key_query.first()

        """If the API key does not exist, raise a 404 Not Found error"""
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with ID: {id} does not exist",
            )

        """Delete the API key and commit the transaction"""
        api_key_query.delete(synchronize_session=False)
        db.commit()

    except HTTPException as http_exception:
        raise http_exception

    except SQLAlchemyError as sqla_error:
        logging.error("SQLAlchemy error occurred: {}".format(str(sqla_error)))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
