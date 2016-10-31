#coding=utf-8
from ..models import Comment, Permission, db, Post
from . import  api
from flask import request, current_app, url_for, jsonify, g
from .decorators import permission_required


@api.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,
                                                        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
                                                        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev' :prev,
        'next' :next,
        'count': pagination.tatal
    })


@api.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/posts/<int:id>/comments/')
def get_posts_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page,
                                                per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
                                                error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)
    return jsonify({
        'posts': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/post/<int:id>/comments/,methods=[post]')
@permission_required(Permission.COMMENT)
def new_post_comments(id):
    post = Post.get_or_404(id)
    comment = Comment.from_json(request.json)                               #这句话到底什么意思？？？？？？？？？？
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)                                                #此处也使用了to_json
    return jsonify(comment.to_json()), 201,\
           {'Location': url_for('api.get_comment',id=comment.id,_external=True)}
