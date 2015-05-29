#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Michael Perzel
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: bigip_gtm_virtual_server
short_description: "Manages F5 BIG-IP GTM virtual servers"
description:
    - "Manages F5 BIG-IP GTM virtual servers"
version_added: "1.9"
author: 'Michael Perzel'
notes:
    - "Requires BIG-IP software version >= 11.4"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Tested with manager and above account privilege level"

requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - BIG-IP username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - BIG-IP password
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Virtual server state
        required: true
        choices: ['present', 'absent','enabled','disabled']
        aliases: []
    virtual_server_name:
        description:
            - Virtual server name
        required: True
        default: null
        aliases: []
    virtual_server_server:
        description:
            - Virtual server server
        required: true
        default: null
        aliases: []
'''

EXAMPLES = '''
  - name: Enable virtual server
    local_action: >
      bigip_gtm_virtual_server
      server=192.168.0.1
      user=admin
      password=mysecret
      virtual_server_name=myname
      virtual_server_server=myserver
      state=enabled
'''

try:
    import bigsuds
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

def bigip_api(bigip, user, password):
    api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
    return api

def virtual_server_exists(api, name, server):
    # hack to determine if pool exists
    result = False
    try:
        virtual_server_id = {'name': name, 'server': server}
        api.GlobalLB.VirtualServerV2.get_object_status([virtual_server_id])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def get_virtual_server_state(api, name, server):
    virtual_server_id = {'name': name, 'server': server}
    state = api.GlobalLB.VirtualServerV2.get_enabled_state([virtual_server_id])
    state = state[0].split('STATE_')[1].lower()
    return state

def set_virtual_server_state(api, name, server, state):
    virtual_server_id = {'name': name, 'server': server}
    state = "STATE_%s" % state.strip().upper()
    api.GlobalLB.VirtualServerV2.set_enabled_state([virtual_server_id], [state])

def main():
    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True),
            state = dict(type='str', required=True, choices=['present', 'absent', 'enabled', 'disabled']),
            virtual_server_name = dict(type='str', required=True),
            virtual_server_server = dict(type='str', required=True)
        ),
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    virtual_server_name = module.params['virtual_server_name']
    virtual_server_server = module.params['virtual_server_server']
    state = module.params['state']

    result = {'changed': False}  # default

    try:
        api = bigip_api(server, user, password)

        if not virtual_server_exists(api, virtual_server_name, virtual_server_server):
            module.fail_json(msg="virtual server does not exist")

        if state == 'absent':
            if not module.check_mode:
                # Stub
                remove_virtual_server(api, pool, virtual_server_name, virtual_server_server)
                result = {'changed': True, 'deleted': deleted}
            else:
                result = {'changed': True}
        elif state == 'present':
            if not module.check_mode:
                # Stub
                add_virtual_server(api, pool, virtual_server_name, virtual_server_server)
                result = {'changed': True}
            else:
                # Stub
                # virtual server exists -- potentially modify attributes
                result = {'changed': True}
        elif state == 'enabled':
            if state != get_virtual_server_state(api, virtual_server_name, virtual_server_server):
                if not module.check_mode:
                    set_virtual_server_state(api, virtual_server_name, virtual_server_server, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}
        elif state == 'disabled':
            if state != get_virtual_server_state(api, virtual_server_name, virtual_server_server):
                if not module.check_mode:
                    set_virtual_server_state(api, virtual_server_name, virtual_server_server, state)
                    result = {'changed': True}
                else:
                    result = {'changed': True}

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
