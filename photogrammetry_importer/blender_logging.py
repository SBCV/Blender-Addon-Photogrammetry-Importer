import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def log_report(output_type, some_str, op=None):
    # output_type is one of: 'INFO', 'WARNING' or 'ERROR'
    logger.info(output_type + ': ' + some_str)
    if op is not None:
        op.report({output_type}, some_str)

