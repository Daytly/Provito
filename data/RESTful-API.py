from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource

from data import db_session
from data.advertisement import Advertisement

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('is_private', required=True, type=bool)
parser.add_argument('is_published', required=True, type=bool)
parser.add_argument('user_id', required=True, type=int)


def abort_if_advertisement_not_found(advertisement_id):
    session = db_session.create_session()
    advertisement = session.query(Advertisement).get(advertisement_id)
    if not advertisement:
        abort(404, message=f"Advertisement {advertisement_id} not found")


class AdvertisementResource(Resource):
    def get(self, advertisement_id):
        abort_if_advertisement_not_found(advertisement_id)
        session = db_session.create_session()
        advertisement = session.query(Advertisement).get(advertisement_id)
        return jsonify({'advertisement': advertisement.to_dict(
            only=('title', 'content', 'user_id', 'is_private'))})

    def delete(self, advertisement_id):
        abort_if_advertisement_not_found(advertisement_id)
        session = db_session.create_session()
        advertisement = session.query(Advertisement).get(advertisement_id)
        session.delete(advertisement)
        session.commit()
        return jsonify({'success': 'OK'})


class AdvertisementListResource(Resource):
    def get(self):
        session = db_session.create_session()
        advertisement = session.query(Advertisement).all()
        return jsonify({'advertisement': [item.to_dict(
            only=('title', 'content', 'user.name')) for item in advertisement]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        advertisement = Advertisement(
            title=args['title'],
            content=args['content'],
            user_id=args['user_id'],
            is_published=args['is_published'],
            is_private=args['is_private']
        )
        session.add(advertisement)
        session.commit()
        return jsonify({'success': 'OK'})