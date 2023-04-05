import flask
from flask import jsonify

from . import db_session
from .advertisement import Advertisement

blueprint = flask.Blueprint(
    'advertisement_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/advertisement')
def get_advertisement():
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).all()
    return jsonify(
        {
            'advertisement':
                [item.to_dict(only=('title', 'content', 'user.name'))
                 for item in advertisement]
        }
    )


@blueprint.route('/api/advertisement/<int:advertisement_id>', methods=['GET'])
def get_one_advertisement(advertisement_id):
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).get(advertisement_id)
    if not advertisement:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'advertisement': advertisement.to_dict(only=(
                'title', 'content', 'user_id', 'is_private'))
        }
    )


@blueprint.route('/api/advertisement', methods=['POST'])
def create_advertisement():
    if not flask.request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in flask.request.json for key in
                 ['title', 'content', 'user_id', 'is_private']):
        return jsonify({'error': 'Bad request'})
    db_sess = db_session.create_session()
    advertisement = Advertisement(
        title=flask.request.json['title'],
        content=flask.request.json['content'],
        user_id=flask.request.json['user_id'],
        is_private=flask.request.json['is_private']
    )
    db_sess.add(advertisement)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/advertisement/<int:advertisement_id>', methods=['DELETE'])
def delete_advertisement(advertisement_id):
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).get(advertisement_id)
    if not advertisement:
        return jsonify({'error': 'Not found'})
    db_sess.delete(advertisement)
    db_sess.commit()
    return jsonify({'success': 'OK'})
