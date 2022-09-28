
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
setup_db(app)
CORS(app)


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks")
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def get_drink_detail(payload):
    drinks = Drink.query.all()
    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drink(payload):
    body = request.get_json()
    drink_title = body.get('title', None)
    drink_recipe = body.get('recipe', None)

    if drink_title is None or drink_recipe is None:
        abort(422)

    try:
        if isinstance(drink_recipe, dict):
            new_drink = Drink(title=drink_title,
                              recipe=json.dumps([drink_title]))
        else:
            new_drink = Drink(title=drink_title,
                              recipe=json.dumps(drink_recipe))

        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        })
    except:
        db.session.rollback()
        raise AuthError({
            'code': 'Drink with the specified title exists already',
            'description': 'The drink title must be unique for every drink.'
        }, 422)
    finally:
        db.session.close()


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()
    drink_title = body.get('title', None)
    drink_recipe = request.args.get('recipe', None)
    try:
        drink_to_update = Drink.query.filter(
            Drink.id == int(drink_id)).one_or_none()

        if drink_to_update is None:
            abort(404)

        if drink_title:
            drink_to_update.title = drink_title

        if drink_recipe:
            if isinstance(drink_recipe, dict):
                recipe_array = json.loads(drink_to_update.recipe)
                recipe_array.append(drink_recipe)
                drink_to_update.recipe = recipe_array
            else:
                drink_to_update.recipe = json.dumps(drink_recipe)
        drink_to_update.update()

        return jsonify({
            'success': True,
            'drinks': [drink_to_update.long()]
        })
    except:
        db.session.rollback()
        abort(422)
    finally:
        db.session.close()


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(payload, drink_id):
    print(drink_id)
    try:
        drink_to_delete = Drink.query.filter(
            Drink.id == int(drink_id)).one_or_none()
        if drink_to_delete is None:
            abort(404)
        drink_to_delete.delete()

        return jsonify({
            "success": True,
            "delete": drink_to_delete.id
        })
    except:
        abort(400)
    finally:
        db.session.close()


        # Error Handling
'''
Example error handling for unprocessable entity
'''


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@ app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@ app.errorhandler(401)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@ app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "method not allowed"
    }), 405


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def handle_auth_error(auth_error):
    return jsonify({
        "success": False,
        "error": auth_error.status_code,
        "message": auth_error.error['description']
    }), auth_error.status_code
