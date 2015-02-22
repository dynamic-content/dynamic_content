from framework.machinery import component
from framework.util.py34 import hashlib
import os
import logging
from framework.includes import SettingsDict
from . import model

__author__ = 'Justus Adam'

_value_mapping = {
    'email': 'email_address'
}

# The following values are special user groups and users
# and very important for the software
#
# you may assign any (integer) value to them
# as long as no two of them are the same
#
# do NOT change these values after installing
# unless you reset the database and reinstall
CONTROL_GROUP_NR = 0

model.User.create_table(fail_silently=True)
model.AccessGroup.create_table(fail_silently=True)

# special access groups
UNKNOWN_GRP = -1  # placeholder - user group undetermined
CONTROL_GROUP = model.AccessGroup.get_or_create(oid=CONTROL_GROUP_NR, machine_name='control_group')
GUEST_GRP = model.AccessGroup.get_or_create(oid=1, machine_name='_GUEST_GROUP')  # Not an authenticated User
AUTH = model.AccessGroup.get_or_create(oid=2, machine_name='_AUTH')  # Default group for users. users that have no particular group assigned to them

# special usernames
UNKNOWN = -1  # placeholder - user undetermined
GUEST = model.User.get_or_create(oid=0, username='_GUEST', access_group=GUEST_GRP, email_address='test@test')  # Not a authenticated User


@component.inject(SettingsDict)
def hash_password(settings, password, salt):
    return hashlib.pbkdf2_hmac(
        settings['hashing_algorithm'],
        password,
        salt,
        settings['hashing_rounds'],
        settings['hash_length']
    )


def check_ident(password, salt, comp_hash):
    hashed = hash_password(password.encode(), salt)
    return hashed == bytes(comp_hash)


@component.inject(SettingsDict)
def hash_and_new_salt(settings, password):
    salt = os.urandom(settings['salt_length'])
    hashed = hash_password(password.encode(), salt)
    return hashed, salt


def get_user(user:str):
    if isinstance(user, model.User):
        return user
    elif isinstance(user, int) or user.isdigit():
        return model.User.get(model.User.oid == user)
    else:
        return model.User.get(model.User.username == user)


def acc_grp(user):
    result = get_user(user)
    if result:
        return result.access_group
    else:
        return AUTH


def add_acc_grp(name, aid=-1):
    if aid != -1:
        model.AccessGroup.create(machine_name=name, oid=aid)
    else:
        model.AccessGroup.create(machine_name=name)


def check_permission(aid, permission, strict=False):
    personal = model.AccessGroupPermission.select().where(model.AccessGroupPermission.group == aid,
                                                          model.AccessGroupPermission.permission == permission)
    if aid != GUEST_GRP and not strict:
        general = model.AccessGroupPermission.select().where(model.AccessGroupPermission.group == AUTH,
                                                             model.AccessGroupPermission.permission == permission)
        return personal.wrapped_count() != 0 or general.wrapped_count() != 0
    else:
        return personal.wrapped_count() != 0


def assign_permission(aid, permission):
    if aid == CONTROL_GROUP_NR:
        logging.getLogger(__name__).error(
            'users, permissions, assign_permission: '
            'cannot assign permissions to control group'
        )
    elif check_permission(aid=aid, permission=permission, strict=True):
        logging.getLogger(__name__).warning(
            'in users, permissions, assign_permission:',
            'access group {} already owns permission {}'.format(aid, permission)
        )
    elif not check_permission(aid=CONTROL_GROUP_NR, permission=permission):
        logging.getLogger(__name__).warning(
            'users, permissions, assign_permission:',
            'permission {} does not exist yet'.format(permission)
        )
        new_permission(permission)
        assign_permission(aid, permission)
    else:
        model.AccessGroupPermission.create(group=aid, permission=permission)


def revoke_permission(aid, permission):
    if aid == CONTROL_GROUP_NR:
        logging.getLogger(__name__).error(
            'users, permissions, assign_permission: '
            'cannot revoke permissions from control group'
        )
    else:
        model.AccessGroupPermission(group=aid, permission=permission).delete_instance()


def new_permission(permission):
    result = model.AccessGroupPermission.select().where(
        model.AccessGroupPermission.group == CONTROL_GROUP_NR,
        model.AccessGroupPermission.permission == permission
    )
    if result.wrapped_count() == 0:
        model.AccessGroupPermission.create(group=CONTROL_GROUP_NR, permission=permission)


def remove_permission(permission):
    model.AccessGroupPermission.delete().where(model.AccessGroup.permission == permission)


def add_user(username, password, email, first_name='', middle_name='', last_name='', access_group=AUTH):
    a = model.User.create(
        username=username,
        email_address=email,
        first_name=first_name,
        last_name=last_name,
        access_group=access_group,
        middle_name=middle_name
    )
    passwd, salt = hash_and_new_salt(password)
    model.UserAuth.create(uid=a,
                          password=passwd,
                          salt=salt)
    return a


def assign_access_group(user, group):
    user = get_single_user(user)
    user.access_group = get_acc_grp(group)
    user.save()


def get_acc_grp(name_or_id:str):
    return model.AccessGroup.get(oid=int(name_or_id)) if isinstance(name_or_id, (
    int, float)) or name_or_id.isnumeric() else model.AccessGroup.get(machine_name=name_or_id)


def get_info(selection):
    return model.User.select().limit(selection)


def get_single_user(uname_or_uid):
    return get_user(uname_or_uid)


def edit_user(user_id, **kwargs):
    user = model.User.get(uid=user_id)
    for argument in kwargs:
        if argument in _value_mapping:
            setattr(user, _value_mapping[argument], kwargs[argument])
        else:
            setattr(user, argument, kwargs[argument])
    user.save()
