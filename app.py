import os
import sys

from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.contrib.cache import SimpleCache

from repositories import WebhookRepository, UserRepository
from services import TwitCastingApiService, PostWebhookOkResponse, DeleteWebhookOkResponse

app = Flask(__name__)
cache = SimpleCache()

client_id = os.getenv('CLIENT_ID', None)
client_secret = os.getenv('CLIENT_SECRET', None)
if client_id is None or client_secret is None:
    app.logger.critical('Please set CLIENT_ID and CLIENT_SECRET')
    sys.exit(1)

base_url = 'https://apiv2.twitcasting.tv'

app.secret_key = b'ccf0943d45f10b6e5a043c731029c15e'


@app.route('/')
def index():
    twit_casting_api_service = TwitCastingApiService(base_url, client_id, client_secret, app.logger)
    user_repository = UserRepository(twit_casting_api_service, cache)
    webhook_repository = WebhookRepository(twit_casting_api_service, app.logger)
    webhooks = webhook_repository.get_all(user_repository)

    return render_template(
        'index.html',
        webhooks=webhooks
    )


@app.route('/add', methods=['POST'])
def add():
    user_id = request.form['user_id']

    twit_casting_api_service = TwitCastingApiService(base_url, client_id, client_secret, app.logger)
    user_repository = UserRepository(twit_casting_api_service, cache)
    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('user "%s" is not found' % user_id, "failure")
        return redirect(url_for("index"))

    response = twit_casting_api_service.post_webhooks(user.id, True, True)
    if isinstance(response, PostWebhookOkResponse):
        flash('Successfully added: %s (%s)' % (user.screen_id, user.id), "success")
    else:
        flash('Failed. status: %s, message: %s' % (response.code, response.message), "failure")

    return redirect(url_for("index"))


@app.route('/delete/<user_id>', methods=['POST'])
def remove(user_id: str):
    twit_casting_api_service = TwitCastingApiService(base_url, client_id, client_secret, app.logger)
    response = twit_casting_api_service.delete_webhooks(user_id, True, True)
    user_repository = UserRepository(twit_casting_api_service, cache)
    user = user_repository.get_by_id(user_id)

    if isinstance(response, DeleteWebhookOkResponse):
        flash("Successfully deleted: %s (%s)" % (user.screen_id, user_id), "success")
    else:
        flash("Failed. status %s, message: %s" % (response.code, response.message), "failure")

    return redirect(url_for("index"))
