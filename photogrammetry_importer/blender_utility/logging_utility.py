import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger()


def log_report(output_type, some_str, op=None):
    """ Write a string to the console and to Blender's info area."""
    # output_type is one of: 'INFO', 'WARNING' or 'ERROR'
    _logger.info(output_type + ": " + some_str)
    if op is not None:
        op.report({output_type}, some_str)
