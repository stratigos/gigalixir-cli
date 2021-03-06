import requests
from . import auth
from . import netrc
import logging
import urllib
import click
import stripe
import json
from six.moves.urllib.parse import quote

def create(host, email, password, accept_terms_of_service_and_privacy_policy):
    r = requests.post('%s/api/free_users' % host, headers = {
        'Content-Type': 'application/json',
    }, json = {
        'email': email,
        'password': password,
    })
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)
    logging.getLogger("gigalixir-cli").info('Created account for %s. Confirmation email sent.' % email)
    logging.getLogger("gigalixir-cli").info('Please check your email and click confirm before continuing.')

def upgrade(host):
    r = requests.put('%s/api/users/upgrade' % host, headers = {
        'Content-Type': 'application/json',
    })
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)
    logging.getLogger("gigalixir-cli").info('Account upgraded.')

def validate_email(host, email):
    r = requests.get('%s/api/validate_email' % host, headers = {
        'Content-Type': 'application/json',
    }, params = {
        "email": email
    })
    if r.status_code != 200:
        errors = json.loads(r.text)["errors"]
        raise Exception("\n".join(errors))

def validate_password(host, password):
    if len(password) < 4:
        raise Exception("Password should be at least 4 characters.")

def change_password(host, email, current_password, new_password):
    r = requests.patch('%s/api/users' % host, auth = (quote(email.encode('utf-8')), quote(current_password.encode('utf-8'))), json = {
        "new_password": new_password
    })
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)

def logout():
    netrc.clear_netrc()

def login(host, email, password, yes):
    r = requests.get('%s/api/login' % host, auth = (quote(email.encode('utf-8')), quote(password.encode('utf-8'))))
    if r.status_code != 200:
        if r.status_code == 401:
            raise Exception("Sorry, we could not authenticate you. If you need to reset your password, run `gigalixir send_reset_password_token --email=%s`." % email)
        raise Exception(r.text)
    else:
        key = json.loads(r.text)["data"]["key"]
        if yes or click.confirm('Would you like us to save your api key to your ~/.netrc file?', default=True):
            netrc.update_netrc(email, key)
            logging.getLogger("gigalixir-cli").info('Logged in as %s.' % email)
        else:
            logging.getLogger("gigalixir-cli").warn('Please edit your ~/.netrc file manually. Many GIGALIXIR CLI commands may not work unless your ~/.netrc file contains your GIGALIXIR credentials.')
            logging.getLogger("gigalixir-cli").info('Add the following:')
            logging.getLogger("gigalixir-cli").info('')
            logging.getLogger("gigalixir-cli").info('machine api.gigalixir.com')
            logging.getLogger("gigalixir-cli").info('\tlogin %s' % email)
            logging.getLogger("gigalixir-cli").info('\tpassword %s' % key)
            logging.getLogger("gigalixir-cli").info('machine git.gigalixir.com')
            logging.getLogger("gigalixir-cli").info('\tlogin %s' % email)
            logging.getLogger("gigalixir-cli").info('\tpassword %s' % key)

def get_reset_password_token(host, email):
    r = requests.put('%s/api/users/reset_password' % host, json = {"email": email})
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        errors = json.loads(r.text)["errors"]
        raise Exception("\n".join(errors))
    else:
        logging.getLogger("gigalixir-cli").info("Reset password token has been sent to your email.")

def reset_password(host, token, password):
    r = requests.post('%s/api/users/reset_password' % host, json = {"token": token, "password": password})
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)

def get_confirmation_token(host, email):
    r = requests.put('%s/api/users/reconfirm_email' % host, json = {"email": email})
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)
    else:
        logging.getLogger("gigalixir-cli").info("Confirmation token has been sent to your email.")

def account(host):
    r = requests.get('%s/api/users' % host)
    if r.status_code != 200:
        if r.status_code == 401:
            raise auth.AuthException()
        raise Exception(r.text)
    else:
        data = json.loads(r.text)["data"]
        click.echo(json.dumps(data, indent=2, sort_keys=True))
