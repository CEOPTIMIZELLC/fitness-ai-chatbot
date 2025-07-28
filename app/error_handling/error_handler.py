from flask import jsonify
from logging_config import logger

def not_found_error(e):
    logger.error(str(e))
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 404

def empty_form_error(e):
    logger.error(str(e))
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 400

def unauthorized_error(e):
    logger.error(str(e))
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 401

