from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from app.config.settings import settings
logger = settings.get_logger()

from app.schemas.request_model import (
    DrugRequest
)

from app.schemas.response_model import (
    DrugResponse
)

from app.services.drug_service import (
    DrugService
)

router = APIRouter(
    prefix="/drug",
    tags=["Drug Information Assistant"]
)

drug_service = DrugService()


@router.post(
    "/information",
    response_model=DrugResponse,
    status_code=status.HTTP_200_OK
)
async def get_drug_information(
    request: DrugRequest
):

    try:

        logger.info(
            f"Drug information request received for: "
            f"{request.drug_name}"
        )

        response = (
            drug_service.get_drug_information(
                drug_name=request.drug_name
            )
        )

        logger.success(
            f"Drug information generated successfully "
            f"for: {request.drug_name}"
        )

        return response

    except ValueError as ex:

        logger.error(
            f"Validation Error: {str(ex)}"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex)
        )

    except Exception as ex:

        logger.exception(
            "Unexpected error occurred while "
            "processing drug information request"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def health_check():

    logger.info(
        "Drug Information Assistant Health Check"
    )

    return {
        "status": "UP",
        "service": "Drug Information Assistant",
        "message": "Service is running successfully"
    }