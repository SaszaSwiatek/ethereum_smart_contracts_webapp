from flask import json, jsonify, request
from . import product_api_blueprint
from models import db, Product, Contract,Attachment
from .api.UserClient import UserClient
from sqlalchemy import or_
from datetime import datetime

@product_api_blueprint.route("/api/product/docs.json", methods=['GET'])
def swagger_api_docs_yml():
    with open('swagger.json') as fd:
        json_data = json.load(fd)

    return jsonify(json_data)


@product_api_blueprint.route('/api/products', methods=['GET'])
def products():

    items = []
    for row in Product.query.all():
        items.append(row.to_json())

    response = jsonify({
            'results' : items
        })

    return response


@product_api_blueprint.route('/api/product/<slug>', methods=['GET'])
def product(slug):
    item = Product.query.filter_by(slug=slug).first()
    if item is not None:
        response = jsonify({'result' : item.to_json() })
    else:
        response = jsonify({'message': 'Cannot find product'}), 404

    return response


@product_api_blueprint.route('/api/product/create', methods=['POST'])
def post_create():

    name = request.form['name']
    slug = request.form['slug']
    image = request.form['image']
    price = request.form['price']

    item = Product()
    item.name = name
    item.slug = slug
    item.image = image
    item.price = price

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Product added', 'product': item.to_json()})

    return response

@product_api_blueprint.route('/api/add-contract', methods=['POST'])
def product_add_contract():

    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    if int(user['id']) == int(request.form['contractor_user_id']):
        return make_response(jsonify({'message': 'user can not sign contract with himself'}), 401)
    contract_instance = Contract()
    contract_instance.title = request.form['title']
    contract_instance.content = request.form['content']
    contract_instance.user_id = int(user['id'])
    contract_instance.contractor_user_id = request.form['contractor_user_id']
    contract_instance.contract_template_id = request.form['contract_template_id']
    contract_instance.value = request.form['value']
    contract_instance.duedate = request.form['duedate']

    db.session.add(contract_instance)
    db.session.commit()

    response = jsonify({'result': contract_instance.to_json()})

    return response

@product_api_blueprint.route('/api/contracts', methods=['GET'])
def contracts():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)
    user = response['result']
    items = []
    rows = Contract.query.filter(or_(Contract.user_id==user['id'], Contract.contractor_user_id==user['id'])).filter(Contract.is_deleted==0).all()
    #.filter(Contract.is_deleted==False)
    if rows is not None:
        for row in rows:
            items.append(row.to_json())
        response = jsonify({
            'results' : items
        })
    else:
        response = jsonify({'message': 'There are no contracts for this user'}), 404

    return response

@product_api_blueprint.route('/api/contract/<contract_title>/exists', methods=['GET'])
def does_contract_title_exists(contract_title):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)
    user = response['result']   
    item = Contract.query.filter_by(title=contract_title,user_id=user['id']).first()
    if item is not None:
        response = jsonify({'result': True})
    else:
        response = jsonify({'message': 'Cannot find contract title'}), 404

    return response

@product_api_blueprint.route('/api/contract/<contract_id>', methods=['GET'])
def contract(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return jsonify({'message': 'Not logged in'}), 401
    item = Contract.query.filter_by(id=contract_id).first()
    if item is not None:
        response = jsonify({'message': 'success','result' : item.to_json() })
    else:
        response = jsonify({'message': 'Cannot find contract','result' : []}), 404

    return response

@product_api_blueprint.route('/api/contract/<contract_id>/delete', methods=['POST'])
def delete_contract(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)
    user = response['result']
    contract_row = Contract.query.filter_by(id=contract_id).first()
    if contract_row is None:
        return jsonify({'message': 'Cannot find contract','result' : []}), 404
    if user['id'] != contract_row.user_id:
        return jsonify({'message': 'You are not allowed to delete the contract','result' : []}), 404
    
    contract_row.is_deleted = True
    contract_row.deleted_timestamp = datetime.utcnow()

    db.session.commit()

    response = jsonify({'message': 'success'})

    return response

@product_api_blueprint.route('/api/contract/<contract_id>/contract_set_as_deployed', methods=['POST'])
def contract_set_as_deployed(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)
    user = response['result']
    contract_row = Contract.query.filter_by(id=contract_id).first()
    if contract_row is None:
        return jsonify({'message': 'Cannot find contract','result' : []}), 404
    if user['id'] != contract_row.contractor_user_id:
        return jsonify({'message': 'You are not allowed to delete the contract','result' : []}), 404
    
    contract_row.contractor_approval_timestamp = datetime.utcnow()
    contract_row.contractor_approval = True
    contract_row.deployment_timestamp = datetime.utcnow()
    contract_row.transaction_hash = request.form['contractAddress']
    contract_row.is_deployed = True
    
    db.session.commit()

    response = jsonify({'message': 'success'})

    return response

@product_api_blueprint.route('/api/contract/<contract_id>/contract_set_as_finalized', methods=['POST'])
def contract_set_as_finalized(contract_id):
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)
    user = response['result']
    contract_row = Contract.query.filter_by(id=contract_id).first()
    if contract_row is None:
        return jsonify({'message': 'Cannot find contract','result' : []}), 404
    if user['id'] != contract_row.user_id:
        return jsonify({'message': 'You are not allowed to finalize the contract','result' : []}), 404
    
    contract_row.finalization_timestamp = datetime.utcnow()
    contract_row.is_finalized = True
    
    db.session.commit()

    response = jsonify({'message': 'success'})

    return response

@product_api_blueprint.route('/api/add_attachment', methods=['POST'])
def add_attachment():

    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    if int(user['id']) != int(request.form['contractor_user_id']):
        return make_response(jsonify({'message': 'user can not add an attachment'}), 401)
    attachment_instance = Attachment()
    attachment_instance.name = request.form['title']
    attachment_instance.filename = request.form['filename']
    attachment_instance.contract_id = request.form['contract_id']
    attachment_instance.description = request.form['description']

    db.session.add(attachment_instance)
    db.session.commit()

    response = jsonify({'message': 'success'})

    return response