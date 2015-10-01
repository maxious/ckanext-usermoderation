import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.lib.helpers as h

from ckan.common import OrderedDict, c, g, request, _

get_action = logic.get_action
import ckan.logic.action as logic_action
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.navl.dictization_functions import validate
import ckan.lib.mailer as mailer
from ckan.model import User as UserModel
from controller import all_account_requests


def user_invite(context, data_dict):
    logic.check_access('user_invite', context, data_dict)

    schema = context.get('schema',
                         logic.schema.default_user_invite_schema())
    data, errors = validate(data_dict, schema, context)
    if errors:
        raise logic.ValidationError(errors)

    user = UserModel.by_email(data_dict['email'])
    if not user:
        return logic_action.create.user_invite(context, data_dict)
    user = user[0]
    member_dict = {
        'username': user.id,
        'id': data['group_id'],
        'role': data['role']
    }
    logic.get_action('group_member_create')(context, member_dict)
    mailer.send_invite(user)
    return model_dictize.user_dictize(user, context)


def get_agencies():
    return ([{'text': group['display_name'], 'value': str(group['name'])} for group in
             logic.get_action('organization_list')(None, {'all_fields': True})],
            logic.get_action('member_roles_list')(None, {'group_type': 'organization'})
            )


def get_used_organizations():
    orgs = []
    try:
        list_of_orgs = get_action('organization_list')({}, {'all_fields': True})
    except Exception:
        orgs = []
    else:
        orgs = [item for item in list_of_orgs if item['packages'] > 0]

    page = h.Page(
        collection=orgs,
        page=request.params.get('page', 1),
        url=h.pager_url,
        items_per_page=20
    )
    return page


class UserModerationPlugin(plugins.SingletonPlugin,
                   tk.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)

    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)

    def get_actions(self):
        return {'user_invite': user_invite}

    def before_map(self, map):
        map.connect('login_by_email', '/user/login_by_email',
                    controller='ckanext.usermoderation.controller:UserModerationController', action='login_by_email')
        map.connect('request_account', '/user/request_account',
                    controller='ckanext.usermoderation.controller:UserModerationController', action='request_account')
        map.connect('account_requests', '/ckan-admin/account_requests',
                    controller='ckanext.usermoderation.controller:UserModerationController', action='account_requests')
        map.connect('account_requests_management', '/ckan-admin/account_requests_management',
                    controller='ckanext.usermoderation.controller:UserModerationController', action='account_requests_management')
        return map

    def get_helpers(self):
        return {
                'count_account_requests': lambda: len(all_account_requests()),
                'get_agencies': get_agencies,
                'get_used_orgs': get_used_organizations}


    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_public_directory(config, 'public')

        # Add this plugin's fanstatic dir.
        tk.add_resource('fanstatic', 'ckanext-usermoderation')
