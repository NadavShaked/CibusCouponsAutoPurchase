import logging
from datetime import datetime
import http.client
import json
import sys
# import azure.functions as func

test_mode = False

cibus_auth_url = 'api.capir.pluxee.co.il'
cibus_auth_authority_header = 'capir.mysodexo.co.il'

cibus_url = 'api.consumers.pluxee.co.il'
cibus_authority_header = 'api.mysodexo.co.il'
cibus_accept_header = 'application/json, text/plain, */*'
cibus_accept_language_header = 'he'
cibus_application_id_header = 'E5D5FEF5-A05E-4C64-AEBA-BA0CECA0E402'
cibus_content_type_header = 'application/json; charset=UTF-8'
cibus_cache_control = 'no-cache'

comp_id = 2199
restaurant_id = 37829
order_type = 2
address_id = 1000849267
category_id = 4755799


def is_valid_time():
    # Get the current date and time
    current_time = datetime.now()
    logging.info(f'is_valid_time - Current Time: {current_time}')

    # Check if the current day is not Friday or Saturday
    if current_time.weekday() not in [4, 5]:
        # Check if the current time is between 8pm and 9pm
        if 20 <= current_time.hour < 21:
            logging.info('is_valid_time - valid time')
            return True
    logging.info('is_valid_time - Doesn\'t valid time')
    return False


def convert_json_to_string(json_object):
    """
    Converts a JSON object into a JSON string.

    Args:
        json_object (dict): A dictionary representing a JSON object.

    Returns:
        str: A JSON string representation of the input JSON object.
    """
    return json.dumps(json_object)


def get_best_combination(coupon_values_array, target_value, i):
    """
    Calculates the best combination of coupon values that cover the target value,
    taking into account the minimum difference between the total coupons value and the target value,
    and selecting the minimum coupon value for the minimum difference.

    Args:
        coupon_values_array (list): A list of coupon values.
        target_value (int): The target value to be covered by the coupon combination.
        i (int): index at the array - for recursion.

    Returns:
        list: The best combination of coupons that covers the target value.
    """
    if target_value <= 0:
        return [0] * len(coupon_values_array), 0
    elif i < 0:
        return [0] * len(coupon_values_array), sys.maxsize

    # or don't take
    coupon_count_dont_take, coupon_value_dont_take = get_best_combination(coupon_values_array, target_value, i - 1)

    # or took
    coupon_count_take, coupon_value_take = get_best_combination(coupon_values_array, target_value - coupon_values_array[i], i)
    coupon_value_take = coupon_value_take + coupon_values_array[i]
    coupon_count_take[i] += 1

    if coupon_value_dont_take == coupon_value_take:
        dont_take_coupon_count = sum(coupon_count_dont_take)
        take_coupon_count = sum(coupon_count_take)
        if dont_take_coupon_count < take_coupon_count:
            return coupon_count_dont_take, coupon_value_dont_take
        else:
            return coupon_count_take, coupon_value_take
    elif coupon_value_dont_take < coupon_value_take:
        return coupon_count_dont_take, coupon_value_dont_take
    else:
        return coupon_count_take, coupon_value_take


def get_user_token(user_name, password, company):
    """
    Retrieves a user authentication token for the provided user credentials.

    Args:
        user_name (str): The username of the user.
        password (str): The password of the user.
        company (str): The company associated with the user.

    Returns:
        str: A user authentication token if the authentication is successful.
    """
    logging.info('get_user_token - start')

    conn = http.client.HTTPSConnection(cibus_auth_url)

    headers = {
        'authority': cibus_auth_authority_header,
        'accept': cibus_accept_header,
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header
    }

    payload = {
        "username": user_name,
        "password": password,
        "company": company
    }
    payload = convert_json_to_string(payload)

    conn.request('POST', '/auth/authToken', payload, headers)
    res = conn.getresponse()

    data = json.loads(res.read().decode('utf-8'))
    token = data['data']['token']

    logging.info('get_user_token - end')
    return token


def get_user_data(token):
    """
    Retrieves user data including user ID and budget using an authentication token.

    Args:
        token (str): A user authentication token obtained through login.

    Returns:
        tuple: A tuple containing user ID (str) and user budget (float).
    """
    logging.info('get_user_data - start')

    conn = http.client.HTTPSConnection(cibus_url)

    headers = {
        'authority': cibus_authority_header,
        'accept': cibus_accept_header,
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }

    payload = ''

    conn.request('GET', '/api/prx_user_info.py', payload, headers)
    res = conn.getresponse()

    data = json.loads(res.read().decode('utf-8'))
    user_id = data['user_cibus_id']
    user_budget = float(data['budget'])
    logging.info('get_user_data - end')

    return user_id, user_budget


def get_available_coupons(token):
    """
    Retrieves available coupons for the user using an authentication token.

    Args:
        token (str): A user authentication token obtained through login.

    Returns:
        dict: A dictionary containing coupon prices (int) as keys and their respective element IDs (int) as values.
    """
    logging.info('get_available_coupons - start')

    conn = http.client.HTTPSConnection(cibus_url)

    headers = {
        'authority': cibus_authority_header,
        'accept': 'application json, text plain, */*',
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }

    payload = ''

    url = f'/api/rest_menu_tree.py?restaurant_id={restaurant_id}&comp_id={comp_id}&order_type={order_type}&element_type_deep=16&lang=he&address_id={address_id}'

    conn.request('GET', url, payload, headers)
    res = conn.getresponse()

    data = json.loads(res.read().decode('utf-8'))

    coupons_response = data['12'][0]['13']
    coupons = {item['price']: item['element_id'] for item in coupons_response}

    logging.info('get_available_coupons - end')

    return coupons


def get_order_time(token):
    """
    Inserts a coupon item with specific dish ID and price into the user's shopping cart.

    Args:
        token (str): A user authentication token obtained through login.
        dish_id (int): The unique dish ID of the coupon item to be added to the cart.
        dish_price (float): The price of the coupon item.

    Returns:
        bool: True if the coupon item is successfully inserted into the cart, False otherwise.
    """
    logging.info(f'get_order_time - start')

    conn = http.client.HTTPSConnection(cibus_url)
    payload = ''
    headers = {
        'accept': cibus_accept_header,
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'cache-control': cibus_cache_control,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }
    conn.request('GET', f'/api/prx_order_times.py?order_type={order_type}&rest_id={restaurant_id}', payload, headers)
    res = conn.getresponse()

    if not(200 <= res.status <= 299):
        logging.error(f'get_order_time, response: {res.status}')
        logging.error('get_order_time - failed')
        return False

    data = json.loads(res.read().decode('utf-8'))
    order_time = data['timeinfo']['ordtime'][0]['time']

    logging.info(f'get_order_time - end')
    return order_time


def insert_coupon_to_cart(token, dish_id, dish_price):
    """
    Inserts a coupon item with specific dish ID and price into the user's shopping cart.

    Args:
        token (str): A user authentication token obtained through login.
        dish_id (int): The unique dish ID of the coupon item to be added to the cart.
        dish_price (float): The price of the coupon item.

    Returns:
        bool: True if the coupon item is successfully inserted into the cart, False otherwise.
    """
    logging.info(f'insert_coupon_to_cart of value: {dish_price} - start')

    conn = http.client.HTTPSConnection(cibus_url)

    headers = {
        'authority': cibus_authority_header,
        'accept': cibus_accept_header,
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }

    payload = {
        'type': 'prx_add_prod_to_cart',
        'order_type': order_type,
        'dish_list': {
            'category_id': category_id,
            'dish_id': dish_id,
            'dish_price': dish_price,
            'co_owner_id': -1,
            'extra_list': []
        }
    }
    payload = convert_json_to_string(payload)

    conn.request('POST', '/api/main.py', payload, headers)
    res = conn.getresponse()

    if not(200 <= res.status <= 299):
        logging.error(f'insert_coupon_to_cart, response: {res.status}')
        logging.error('insert_coupon_to_cart - failed')
        return False

    data = json.loads(res.read().decode('utf-8'))

    if data['code'] != 0:
        logging.error(f'insert_coupon_to_cart, response: {data["msg"]}')
        logging.error('insert_coupon_to_cart - failed')
        return False

    logging.info(f'insert_coupon_to_cart of value: {dish_price} - end')

    return True


def validate_coupon_inserted_to_cart(token, order_time):
    """
    Validates whether a coupon is successfully inserted into the user's cart for a simulated order.

    Args:
        token (str): A user authentication token obtained through login.
        order_time (str): The desired order time, formatted as "HH:mm".

    Returns:
        bool: True if the coupon is successfully inserted into the cart for the simulated order, False otherwise.
    """
    logging.info('validate_coupon_inserted_to_cart - start')

    conn = http.client.HTTPSConnection(cibus_url)

    headers = {
        'authority': cibus_authority_header,
        'accept': 'application.json, text/plain, */*',
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }

    payload = {
        'type': 'prx_simulate_order',
        'order_time': order_time
    }

    payload = convert_json_to_string(payload)

    conn.request('POST', '/api/main.py', payload, headers)
    res = conn.getresponse()

    if not(200 <= res.status <= 299):
        logging.error(f'insert_coupon_to_cart, response: {res.status}')
        logging.error('insert_coupon_to_cart - failed')
        return False

    data = json.loads(res.read().decode('utf-8'))

    if data['head']['count'] != 1:
        logging.error('insert_coupon_to_cart - failed')
        return False

    logging.info('validate_coupon_inserted_to_cart - end')

    return True


def purchase_coupon(token, user_id, order_time):
    """
    Simulates the purchase of a coupon for a specific user and order time.

    Args:
        token (str): A user authentication token obtained through login.
        user_id (int): The user's identifier.
        order_time (str): The desired order time, formatted as "HH:mm".

    Returns:
        bool: True if the coupon purchase is successfully simulated, False otherwise.
    """
    logging.info('purchase_coupon - start')

    conn = http.client.HTTPSConnection(cibus_url)

    headers = {
        'authority': cibus_authority_header,
        'accept': cibus_accept_header,
        'accept-language': cibus_accept_language_header,
        'application-id': cibus_application_id_header,
        'content-type': cibus_content_type_header,
        'cookie': f'token={token}'
    }

    payload = {
        'type': 'prx_apply_order',
        'order_time': order_time
    }
    payload = convert_json_to_string(payload)

    conn.request('POST', '/api/main.py', payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode('utf-8'))

    # if data['head']['count'] != 1 or data['head']['user_id'] != user_id:
    #     return False

    logging.info('purchase_coupon - end')

    return True


def cibus_coupons_auto_purchase(user_name, password):
    company = 'מיקרוסופט'  # set Cibus user's company

    logging.info('Cibus Purchase Flow - Start')

    token = get_user_token(user_name, password, company)

    user_id, user_budget = get_user_data(token)

    logging.info(f'Cibus Purchase Flow - User Budget: {user_budget}')

    coupons = get_available_coupons(token)

    coupon_values = list(coupons.keys())

    best_coupons_combination, _ = get_best_combination(coupon_values, int(user_budget), len(coupon_values) - 1)

    for i, coupon_value_count in enumerate(best_coupons_combination):
        purchase_times = int(coupon_value_count)
        for j in range(purchase_times):
            coupon_value = coupon_values[i]
            dish_id = coupons[coupon_value]

            token = get_user_token(user_name, password, company)

            order_time = get_order_time(token)

            is_inserted_to_cart = insert_coupon_to_cart(token, dish_id, coupon_value)
            # is_inserted_to_cart = is_inserted_to_cart and validate_coupon_inserted_to_cart(token, order_time)
            logging.info(
                f'coupon insert to card, value: {coupon_value}, {j + 1} of {purchase_times} times - {"success" if is_inserted_to_cart else "failed"}')

            if is_inserted_to_cart:
                is_coupon_purchased = purchase_coupon(token, user_id, order_time)
                logging.info(
                    f'coupon purchased, value: {coupon_value}, {j + 1} of {purchase_times} times - {"success" if is_coupon_purchased else "failed"}')

    logging.info('Cibus Purchase Flow - End')

user_name = ''  # set Cibus user name
password = ''  # set Cibus user's password
cibus_coupons_auto_purchase(user_name, password)
