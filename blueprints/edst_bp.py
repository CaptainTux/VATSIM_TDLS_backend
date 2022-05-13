from collections import defaultdict

from flask import Blueprint, jsonify, request, g
from pymongo import MongoClient

import libs.lib
import libs.edst_lib
import mongo_client

# TODO: write this list to database
EDST_KEYS = ['aircraft', 'type', 'equipment', 'route', 'route_data', 'altitude', 'interim', 'hdg', 'spd',
             'previous_route', 'previous_route_data',
             'hold_data', 'free_text_content', 'beacon', 'cleared_direct']

edst_blueprint = Blueprint('edst', __name__)


@edst_blueprint.before_request
def _get_mongo_clients():
    mongo_client.get_edst_mongo_client()


@edst_blueprint.after_request
def _close_mongo_clients(response):
    mongo_client.close_edst_mongo_client()
    return response


@edst_blueprint.route('/entry/get/<callsign>')
def _get_entry(callsign):
    return jsonify(libs.edst_lib.get_edst_entry(callsign))


@edst_blueprint.route('/entry/amend/generic', methods=['POST'])
def _update_entry():
    post_data = request.get_json()
    if not post_data or 'callsign' not in post_data.keys():
        return jsonify(204)
    callsign = post_data['callsign']
    ret_data = libs.edst_lib.update_edst_entry(callsign, post_data)
    return jsonify(ret_data)


@edst_blueprint.route('/trial/route', methods=['POST'])
def _trial_route_amendment():
    post_data = request.get_json()
    keys = post_data.keys()
    amend_data = libs.edst_lib.get_amended_route(route=post_data['route'],
                                                 route_data=post_data['route_data'] if 'route_data' in keys else None,
                                                 direct_fix=post_data['direct_fix'] if 'direct_fix' in keys else None,
                                                 frd=post_data['frd'] if 'frd' in keys else None,
                                                 dest=post_data['dest']) if 'dest' in keys else None
    return jsonify(amend_data) if amend_data else jsonify(204)


@edst_blueprint.route('/entry/amend/route', methods=['POST'])
def _amend_route():
    post_data = defaultdict(request.get_json())
    keys = post_data.keys()
    amend_data = libs.edst_lib.get_amended_route(route=post_data['route'],
                                                 route_data=post_data['route_data'] if 'route_data' in keys else None,
                                                 direct_fix=post_data['direct_fix'] if 'direct_fix' in keys else None,
                                                 frd=post_data['frd'] if 'frd' in keys else None,
                                                 dest=post_data['dest']) if 'dest' in keys else None
    if amend_data and post_data['callsign']:
        libs.edst_lib.update_edst_entry(post_data['callsign'], amend_data)
    return jsonify(amend_data) if amend_data else jsonify(204)


@edst_blueprint.route('/all')
def _get_all_edst():
    data = libs.edst_lib.get_edst_data()
    return jsonify(data)


@edst_blueprint.route('/fav/<artcc>/ctr')
def _get_ctr_fav(artcc):
    data = libs.edst_lib.get_ctr_fav_data(artcc)
    return jsonify(data)


@edst_blueprint.route('/fav/<artcc>/app')
def _get_app_fav(artcc):
    data = libs.edst_lib.get_app_fav_data(artcc)
    return jsonify(data)


@edst_blueprint.route('/ctr_profiles/<artcc>')
def _get_ctr_profiles(artcc):
    data = libs.edst_lib.get_ctr_profiles(artcc)
    return jsonify(data)


@edst_blueprint.route('/get_beacon/<artcc>')
def _get_beacon(artcc):
    client: MongoClient = g.mongo_reader_client
    data = {d['callsign']: d for d in client.edst.data.find({}, {'_id': False})}
    codes_in_use = [d['beacon'] for d in data.values()]
    code = libs.edst_lib.get_beacon(artcc, codes_in_use)
    return jsonify({'beacon': code})


@edst_blueprint.route('/aar/<artcc>/<cid>', methods=['GET', 'POST'])
def _get_aar(artcc, cid):
    post_data = request.get_json()
    if post_data:
        aar_data = libs.edst_lib.get_edst_aar(artcc, cid, route=post_data['route'])
    else:
        aar_data = libs.edst_lib.get_edst_aar(artcc, cid)
    return jsonify(aar_data)


@edst_blueprint.route('/gpd/<artcc>/sectors')
def _get_gpd_sectors(artcc: str):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].gpd_sectors.find({}, {'_id': False}))
    return jsonify(data)


@edst_blueprint.route('/gpd/<artcc>/airports')
def _get_gpd_airports(artcc: str):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].gpd_airports.find({}, {'_id': False}))
    return jsonify(data)


@edst_blueprint.route('/gpd/<artcc>/navaids')
def _get_gpd_navaids(artcc: str):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].gpd_navaids.find({}, {'_id': False}))
    return jsonify(data)


@edst_blueprint.route('/gpd/<artcc>/waypoints')
def _get_gpd_waypoints(artcc: str):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].gpd_waypoints.find({}, {'_id': False}))
    return jsonify(data)


@edst_blueprint.route('/gpd/<artcc>/airways')
def _get_gpd_airways(artcc: str):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].gpd_airways.find({}, {'_id': False}))
    return jsonify(data)


@edst_blueprint.route('/reference_fixes/<artcc>')
def _get_reference_fix_list(artcc):
    client: MongoClient = g.mongo_reader_client
    data = list(client[artcc.lower()].reference_fixes.find({}, {'_id': False}))
    return jsonify(data)
