from flask import jsonify

def not_found_error(e):
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 404

def empty_form_error(e):
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 400

def unauthorized_error(e):
    return jsonify({
        "status": "error",
        "message": str(e)
    }), 401

