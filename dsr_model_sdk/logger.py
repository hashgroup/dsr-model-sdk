import logging
import sys

logger = logging.getLogger("dataspire-sdk")
logger.setLevel(level=logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(threadName)s | %(processName)s | %(levelname)s | %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(formatter)
logger.addHandler(handler)