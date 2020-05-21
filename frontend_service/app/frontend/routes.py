from flask import render_template, session, redirect, url_for, flash, request
import requests
from flask_login import current_user
from . import forms
from . import frontend_blueprint
from .api.UserClient import UserClient
from .api.OrderClient import OrderClient
from .api.ProductClient import ProductClient
from .api.BlockchainClient import BlockchainClient
from datetime import datetime
import os
from werkzeug import secure_filename

#@staticmethod
#def save_picture(form):
#
#    return filename

# Home page
@frontend_blueprint.route('/', methods=['GET'])
def home():
    # session.clear()
    #nie dziala if current_user.is_authenticated:
        #nie dziala order = order
       #nie dziala session['order'] = OrderClient.get_order_from_session()
    try:
        products = ProductClient.get_products()
    except requests.exceptions.ConnectionError:
        products = {
            'results': []
        }

    return render_template('home/index.html', products=products)

# Contracts page
@frontend_blueprint.route('/contracts', methods=['GET'])
def contracts():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    try:
        contract_items = ProductClient.get_user_contracts()
    except requests.exceptions.ConnectionError:
        contract_items = {
            'results': []
        }
    for contract in contract_items['results']:
        initiator_email_request = UserClient.get_email(contract['user_id'])
        contract['user_id'] = initiator_email_request['result'] if initiator_email_request['message'] == 'success' else initiator_email_request['message']
        contractor_email_request = UserClient.get_email(contract['contractor_user_id'])
        contract['contractor_user_id'] = contractor_email_request['result'] if contractor_email_request['message'] == 'success' else contractor_email_request['message']

    return render_template('contracts/contracts.html', contracts=contract_items)

# Login
@frontend_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    #nie dziala if current_user.is_authenticated:
        #nie dziala return redirect(url_for('frontend.home'))
    if 'user' in session:
        flash('You are already logged in', 'error')
        return redirect(url_for('frontend.home'))
    form = forms.LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            api_key = UserClient.post_login(form)
            if api_key:
                # Get the user
                session['user_api_key'] = api_key
                user = UserClient.get_user()
                session['user'] = user['result']

                # Get the order
                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']

                # Existing user found
                flash('Welcome back, ' + user['result']['username'], 'success')
                return redirect(url_for('frontend.home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login/index.html', form=form)


# Add new contract
@frontend_blueprint.route('/addcontract', methods=['GET', 'POST'])
def addcontract():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    current_user = UserClient.get_user()
    form = forms.AddContract(request.form)
    form.contractor_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.initiator_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.contract_template_id.choices  = [(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate."),(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate.")]

    if request.method == "POST":
        if form.validate_on_submit():
            if BlockchainClient.get_eth_balance(current_user['result']['eth_address'])['eth_balance'] < form.value.data:
                flash('Your ETH balance is lower than a contract value' , 'error')
                return render_template('addcontract/index.html', form=form)
            contract_with_same_title = ProductClient.does_contract_title_exists(form.title.data)
            if contract_with_same_title:
                flash('Contract with that name already exists, please name it differently', 'error')
            else:
                contract = ProductClient.post_add_contract(form)
                if contract:
                    ## sprawdzam czy udalo sie dodac kontrakt Store user ID in session and redirect
                    flash('Thanks for adding your contract', 'success')
                    return redirect(url_for('frontend.contracts'))
                else:
                    flash('Contract adding error, contract was not added', 'error')
        else:
            flash('Errors found in formular', 'error')
    return render_template('addcontract/index.html', form=form)

# Register new customer
@frontend_blueprint.route('/register', methods=['GET', 'POST'])
def register():

    form = forms.RegisterForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data

            # Search for existing user
            user = UserClient.does_exist(username)
            if user:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create the new user
                user = UserClient.post_user_create(form)
                if user:
                    # Store user ID in session and redirect
                    flash('Thanks for registering, please login', 'success')
                    return redirect(url_for('frontend.login'))

        else:
            flash('Formular wrongly filled, please correct your input', 'error')

    return render_template('register/index.html', form=form)

# Logout
@frontend_blueprint.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('frontend.home'))


# Product page
@frontend_blueprint.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):

    # Get the product
    response = ProductClient.get_product(slug)
    item = response['result']

    form = forms.ItemForm(product_id=item['id'])

    if request.method == "POST":

        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('frontend.login'))

        order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
        session['order'] = order['result']
        flash('Order has been updated', 'success')

    return render_template('product/index.html', product=item, form=form)


# ORDER PAGES


# Order summary  page
@frontend_blueprint.route('/checkout', methods=['GET'])
def summary():

    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    order = OrderClient.get_order()

    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    OrderClient.post_checkout()

    return redirect(url_for('frontend.thank_you'))


# Order thank you
@frontend_blueprint.route('/order/thank-you', methods=['GET'])
def thank_you():

    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('frontend.home'))

    session.pop('order', None)
    flash('Thank you for your order', 'success')

    return render_template('order/thankyou.html')

# Order thank you

@frontend_blueprint.route('/wallet', methods=['GET'])
def wallet():

    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    user = UserClient.get_user()
    wallet_items = BlockchainClient.get_eth_balance(user['result']['eth_address'])
    if wallet_items['message'] != 'success':
        flash(wallet_items['message'], 'error')

    return render_template('wallet/index.html', wallet_items=wallet_items)

@frontend_blueprint.route('/maketranfser', methods=['GET', 'POST'])
def maketranfser():

    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    user = UserClient.get_user()
    wallet_items = BlockchainClient.get_eth_balance(user['result']['eth_address'])
    if wallet_items['message'] == 'Blockchain provider not connected':
        flash(wallet_items['message'], 'error')
    form = forms.Maketransfer(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            respone = BlockchainClient.send_transfer(user['result']['eth_address'],form.eth_recipient_address.data,form.value.data,user['result']['eth_prv_key'])
            if respone:
                flash(respone['message'], 'success')
                return redirect(url_for('frontend.wallet'))
            else:
                flash('Transaction execution error', 'error')
        else:
            flash('Formular wrongly filled, please correct your input', 'error')
    return render_template('maketranfser/index.html', wallet_items=wallet_items, form=form)

@frontend_blueprint.route('/contract/<contract_id>', methods=['GET', 'POST'])
def contract(contract_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    current_user = UserClient.get_user()
    response = ProductClient.get_contract(contract_id)
    if response['message'] != 'success':
        flash(response['message'], 'error')
        return redirect(url_for('frontend.home'))

    item = response['result']
    allow_edit = False
    if current_user['result']['id'] == item['user_id'] and item['is_deployed'] == False:
        allow_edit = True

    allow_approval = False
    if current_user['result']['id'] == item['contractor_user_id'] and item['contractor_approval'] == False:
        allow_approval = True

    allow_finalize = False
    if current_user['result']['id'] == item['user_id'] and item['is_deployed'] == True and item['is_finalized'] == False:
        allow_finalize = True

    allow_add_attachment = False
    if current_user['result']['id'] == item['contractor_user_id'] and item['is_deployed'] == True and item['is_finalized'] == False:
        allow_add_attachment = True

    if request.method == "POST" and allow_approval is True:
        #if BlockchainClient.get_eth_balance(current_user['result']['eth_address'])['eth_balance'] < form.value.data:
            #flash('Initiator ETH balance is lower than a contract value' , 'error')
        #else:
        deploy_contract_response = OrderClient.deploy_contract(contract_id)
        if deploy_contract_response['message'] != 'success':
            flash(deploy_contract_response['message'], 'error')
        else:
            flash('Contract successfully deployed', 'success')


    if request.method == "POST" and allow_finalize is True:
        #if BlockchainClient.get_eth_balance(current_user['result']['eth_address'])['eth_balance'] < form.value.data:
            #flash('Initiator ETH balance is lower than a contract value' , 'error')
        #else:
        deploy_contract_response = OrderClient.finalize_contract(contract_id)
        if deploy_contract_response['message'] != 'success':
            flash(deploy_contract_response['message'], 'error')
        else:
            flash('Contract successfully finalized', 'success')

    current_user = UserClient.get_user()
    response = ProductClient.get_contract(contract_id)
    if response['message'] != 'success':
        flash(response['message'], 'error')
        return redirect(url_for('frontend.home'))

    item = response['result']
    allow_edit = False
    if current_user['result']['id'] == item['user_id'] and item['is_deployed'] == False:
        allow_edit = True

    allow_approval = False
    if current_user['result']['id'] == item['contractor_user_id'] and item['contractor_approval'] == False:
        allow_approval = True

    allow_finalize = False
    if current_user['result']['id'] == item['user_id'] and item['is_deployed'] == True and item['is_finalized'] == False:
        allow_finalize = True

    allow_add_attachment = False
    if current_user['result']['id'] == item['contractor_user_id'] and item['is_deployed'] == True and item['is_finalized'] == False:
        allow_add_attachment = True

    form = forms.AddContract(request.form)
    form.contractor_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.initiator_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.contract_template_id.choices  = [(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate."),(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate.")]
    
    form.initiator_user_id.data = item['user_id']
    form.title.data = item['title']
    form.content.data = item['content']
    form.contractor_user_id.data = item['contractor_user_id']
    form.contract_template_id.data = item['contract_template_id']
    form.value.data = item['value']
    form.duedate.data = datetime.fromtimestamp(item['duedate'])
    form.contractor_approval.data = item['contractor_approval']
    form.contractor_approval_timestamp.data = datetime.fromtimestamp(item['contractor_approval_timestamp']) if item['contractor_approval_timestamp'] is not None else None #datetime.fromtimestamp(item['contractor_approval_timestamp'])
    form.is_deployed.data = item['is_deployed']
    form.contract_id.data = item['id']
    form.contract_date_added.data = datetime.fromtimestamp(item['date_added'])
    form.is_finalized.data = item['is_finalized']
    form.finalization_timestamp.data = datetime.fromtimestamp(item['finalization_timestamp']) if item['finalization_timestamp'] is not None else None

    return render_template('contract/index.html', form=form, allow_edit=allow_edit, allow_approval=allow_approval, allow_finalize=allow_finalize, allow_add_attachment=allow_add_attachment)  
        
    #
    #    if 'user' not in session:
    #        flash('Please login', 'error')
    #        return redirect(url_for('frontend.login'))

    #    order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
    #    session['order'] = order['result']
    #    flash('Order has been updated', 'success')

@frontend_blueprint.route('/contract/<contract_id>/edit', methods=['GET', 'POST'])
def editcontract(contract_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    current_user = UserClient.get_user()
    response = ProductClient.get_contract(contract_id)
    if response['message'] != 'success':
        flash(response['message'], 'error')
        return redirect(url_for('frontend.home'))
    item = response['result']
    if current_user['result']['id'] != item['user_id'] or item['is_deployed'] == True:
        flash('You are not allowed to edit that contract', 'error')
        return redirect(url_for('frontend.home'))
    form = forms.AddContract(request.form)
    form.contractor_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.initiator_user_id.choices  = [(user['id'] , user['email']) for user in UserClient.get_users()]
    form.contract_template_id.choices  = [(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate."),(1,"10% paid in advance at contract deployment, rest is paid after your confirmation. The contractor will receive a 10% bonus if contract will be finalized before duedate.")]
   
    if request.method == "POST" and current_user['result']['id'] == item['user_id'] and item['is_deployed'] == False:
        if form.validate_on_submit():
            if BlockchainClient.get_eth_balance(current_user['result']['eth_address'])['eth_balance'] < form.value.data:
                flash('Your ETH balance is lower than a contract value' , 'error')
                return render_template('editcontract/index.html', form=form)

            response_delete_contract = ProductClient.post_delete_contract(item['id'])
            if response_delete_contract['message'] != 'success':
                flash(response_delete_contract['message'] , 'error')
                return redirect(url_for('frontend.contracts'))
            contract = ProductClient.post_add_contract(form)
            if contract:
                ## sprawdzam czy udalo sie dodac kontrakt Store user ID in session and redirect
                flash('Contract updated', 'success')
                return redirect(url_for('frontend.contracts'))
            else:
                flash('Contract adding error, contract was not added', 'error')
        else:
            flash('Errors found in formular', 'error')
    elif request.method == 'GET':
 
        #form.initiator_user_id.data = item['user_id']
        form.title.data = item['title']
        form.content.data = item['content']
        form.contractor_user_id.data = item['contractor_user_id']
        form.contract_template_id.data = item['contract_template_id']
        form.value.data = item['value']
        form.duedate.data = datetime.fromtimestamp(item['duedate'])
        form.contractor_approval.data = item['contractor_approval']
        form.contractor_approval_timestamp.data = datetime.fromtimestamp(item['contractor_approval_timestamp']) if item['contractor_approval_timestamp'] is not None else None #datetime.fromtimestamp(item['contractor_approval_timestamp'])
        form.is_deployed.data = item['is_deployed']
        form.contract_id.data = item['id']
    return render_template('editcontract/index.html', form=form)

@frontend_blueprint.route('/contract/<contract_id>/add_attachment',methods=['GET', 'POST'])
def add_attachment(contract_id):
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('frontend.login'))
    current_user = UserClient.get_user()
    response = ProductClient.get_contract(contract_id)
    if response['message'] != 'success':
        flash(response['message'], 'error')
        return redirect(url_for('frontend.home'))
    item = response['result']

    allow_add_attachment = False
    if current_user['result']['id'] == item['contractor_user_id'] and item['is_deployed'] == True and item['is_finalized'] == False:
        allow_add_attachment = True
    
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!! allow add attachment = ",allow_add_attachment)
    form = forms.AddAttachmentForm(request.form)
    if form.validate_on_submit():
        if form.picture.data:
            print('form.picture.data == true!!!')
            print('form.picture.data == true!!!')
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(form_picture.filename)
            picture_fn = random_hex + f_ext
            picture_path = os.path.join(current_app.root_path, 'static/attachments', picture_fn)

            image_filename = picture_fn
            name = form.name.data
            description = form.description.data
            print('!!!!!!!!!!!!!!!!! image_filename: ',image_filename)
            print('!!!!!!!!!!!!!!!!! name: ',name)
            print('!!!!!!!!!!!!!!!!! description: ',description)

            
            flash('Your account has been updated!', 'success')
            return redirect(url_for('frontend.contracts'))
    image_file = url_for('static', filename='attachments/'+'test_not_realy_real_filename.txt')
    return render_template('add_attachment/index.html', title='Account', image_file=image_file, form=form)

'''
    if request.method == "POST" and allow_add_attachment is True:
        filename = None
        if form.validate_on_submit():
            if form.file_field.data:
                filename = secure_filename(form.file_field.data.filename)
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!filename =",filename)
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!form file data exists!")
                file_data = request.FILES[form.file_field.name].read()
                random_hex = secrets.token_hex(16)
                _, f_ext = os.path.splitext(form.ile_field.data)
                filename = random_hex + f_ext
                file_path = os.path.join(current_app.root_path, 'static/attachments', filename)
                #form.file_field.file.save(file_path)
                #myFile = secure_filename(form.fileName.file.filename)
                #form.fileName.file.save(PATH+myFile)
                open(file_path, 'w').write(file_data)
                
                    
                form.filename.data = filename
                form.contract_id.data = item['id']
                response_add_attachment = ProductClient.add_attachment(form)
                if response['message'] == 'success':
                    flash('Attachment added', 'success')
                    return redirect(url_for('frontend.contracts'))
        else:
            
            flash('Errors found in formular', 'error')
    else:
        filename = None
    return render_template('add_attachment/index.html', form=form, filename=filename)
    #elif request.method == 'GET':
    # Get the product
    #response = ProductClient.get_product(slug)
    #item = response['result']

    #form = forms.ItemForm(product_id=item['id'])

    #if request.method == "POST":

    #    if 'user' not in session:
    #        flash('Please login', 'error')
    #        return redirect(url_for('frontend.login'))
    #
    #    order = OrderClient.post_add_to_cart(product_id=item['id'], qty=1)
    #   session['order'] = order['result']
    #    flash('Order has been updated', 'success')
'''