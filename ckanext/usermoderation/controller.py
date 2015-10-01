from ckan.common import response, request, c
from ckan.controllers.package import PackageController
import ckan.logic as logic
import ckan.plugins.toolkit as tk

import ckan.lib.base as base

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
import cStringIO

import csv

import random
import ckan.model as model
import ckan.lib.mailer as mailer
import ckan.lib.helpers as h
import ckan.lib.dictization.model_dictize as model_dictize
from logging import warn as l


class UserModerationController(PackageController):
    def login_by_email(self):
        login_dict = request.params.copy()
        if '@' in login_dict.get('login'):
            user = model.User.by_email(login_dict['login'].lower())
            if user:
                user = user[0]
                login_dict['login'] = user.name

        tk.redirect_to(request.environ['repoze.who.plugins']['friendlyform'].login_handler_path, **login_dict)

    def request_account(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': model.Session.query(model.User).filter_by(sysadmin=True).first().name
        }
        params = request.params
        data = dict(
            display_name=params['name'],
            fullname=params['name'],
            name=logic.action.create._get_random_username_from_email(params['email']).lower(),
            password=str(random.SystemRandom().random()),
            state=model.State.PENDING,
            email=params['email'],
            about=params['notes'])
        try:
            if model.User.by_email(params['email']): raise logic.ValidationError('Email in use')
            user_dict = logic.get_action('user_create')(context, data)
            member_dict = {
                'username': user_dict['id'],
                'id': params['agency'],
                'role': params['role']
            }

            logic.get_action('organization_member_create')(context, member_dict)
        except logic.ValidationError, e:
            response.status = 400
            return

        msg = "New account's request:\nUsername: {name}\nEmail: {email}\nAgency: {agency}\nRole: {role}\nNotes: {notes}".format(
            **params)
        mailer.mail_recipient('Admin', params['admin'], 'Account request', msg)

    def account_requests(self):  # /ckan-admin/account_requests rendering
        accounts = [{
                        'id': user.id,
                        'name': user.display_name,
                        'email': user.email,
                        'about': user.about,
                        'group': user.get_groups(),
                        'role': model.Session.query(model.Member).filter_by(table_id=user.id).first()
                    } for user in all_account_requests()]
        return base.render('admin/account_requests.html', {'accounts': accounts})

    # apptove or forbid requested account
    def account_requests_management(self):
        action = request.params['action']
        user_id = request.params['id']
        agency_name = request.params['agency']
        user = model.User.get(user_id)

        context = {
            'model': model,
            'session': model.Session,
        }
        if user.get_groups():
            member_dict = {
                'username': user_id,
                'id': user.get_groups()[0].name,
            }
            logic.get_action('organization_member_delete')(context,
                                                           member_dict)  # remove user from organization (if organization or role wrong)

        if action == 'forbid':  # remove user
            logic.get_action('user_delete')(context, {'id': user_id})
        elif action == 'approve':  # add user to some organization
            agency = logic.get_action('organization_show')(context, {'id': agency_name})
            role = request.params['role']
            member_dict = {
                'username': user.id,
                'id': agency_name,
                'role': role

            }
            logic.get_action('organization_member_create')(context, member_dict)

            user.about = None
            mailer.send_invite(user)  # sent activation letter
        response.status = 200


# get list of request (used at /ckan-admin/account_requests)
def all_account_requests():
    return model.Session.query(model.User).filter(model.User.state == 'pending', model.User.about != None).all()
