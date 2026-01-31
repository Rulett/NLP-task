from fastapi import APIRouter

from src.api.v1.router import v1_router

main_router = APIRouter(prefix="/api")
main_router.include_router(v1_router)


@main_router.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    """
    Perform a health check of the service.

    This endpoint is used to verify that the service is running and responsive.
    It returns a simple JSON response indicating the success status of the health check.

    Returns:
        dict[str, str]: A dictionary with a single key-value pair indicating the health status.
                        The key is "Success" and the value is "True".

    Raises:
        HTTPException: If an unexpected error occurs while processing the request,
                       an HTTPException with a 500 status code may be raised.
    """
    return {"Success": "True"}
