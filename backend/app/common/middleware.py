import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..api_keys.models import ApiKey
from ..database import get_db
from .utils import verify_api_key


async def verify_api_key_middleware(request: Request, db: Session = Depends(get_db)):
    """
    Verify the validity of the provided API key for the company.

    Args:
        request (Request): The request object containing additional information.
        db (Session): The database session.

    Raises:
        HTTPException: If the API key is not found, a 403 Forbidden Error is raised.
        HTTPException: If any other unexpected error occurs, a 500 Internal Server Error is raised.
    """
    try:
        apiKey = request.headers.get("X-API-KEY")

        """If no API key is provided, raise a 403 Forbidden error"""
        if not apiKey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="API key is required"
            )

        """Get all API keys and their IDs for the company from the database"""
        user_api_key = db.query(ApiKey.apiKey, ApiKey.apiKey_id).all()

        """If no API keys are found, raise a 403 Forbidden error"""
        if not user_api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No API key found, please create an API key",
            )

        """Check if the provided API key matches any of the API keys in the database"""
        valid_api = False
        for hashed_api_key, api_key_id in user_api_key:
            verification = verify_api_key(apiKey, hashed_api_key)
            if verification:
                valid_api = True
                api_key_id = api_key_id
                break

        """If the API key is not valid, raise a 403 Forbidden error"""
        if not valid_api:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
            )

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
