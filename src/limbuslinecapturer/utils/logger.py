import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("Comparison.log"),
        logging.FileHandler("ParaTranz.log"),
        logging.StreamHandler(),
    ],
)

COMPARISON_LOGGER = logging.getLogger("Comparison")
COMPARISON_LOGGER.setLevel(logging.INFO)

API_LOGGER = logging.getLogger("ParaTranz")
API_LOGGER.setLevel(logging.INFO)
