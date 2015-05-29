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
module: bigip_gtm_facts
short_description: "Collect facts from F5 BIG-IP GTM devices"
description:
    - "Collect facts from F5 BIG-IP GTM devices"
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
    include:
        description:
            - Fact category to collect
        required: true
        choices: ['pool','wide_ip','virtual_server']
        aliases: []
    pool:
        description:
            - Pool name
        required: false
        default: None
        aliases: []
    partition:
        description:
            - Partition name
        required: false
        default: Common
        aliases: []
    wide_ip:
        description:
            - Pool name
        required: false
        default: None
        aliases: []
    virtual_server_name:
        description:
            - Virtual server name
        required: false
        default: None
        aliases: []
    virtual_server_server:
        description:
            - Virtual server server
        required: false
        default: None
        aliases: []
'''

EXAMPLES = '''
  - name: Get pool status
    local_action: >
      bigip_gtm_pool
      server=192.168.0.1
      user=admin
      password=mysecret
      pool=my_pool
      include=pool
      partition=Common
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

def get_all_pools(api):
    try:
        pools = api.GlobalLB.Pool.get_list()
        return pools
    except Exception, e:
        print e

def get_pool_status(api, pool):
    try:
        return api.GlobalLB.Pool.get_object_status([pool])
    except Exception, e:
        print e

def get_pool_member_state(api, pool):
    state = api.GlobalLB.Pool.get_enabled_state([pool])
    state = state[0].split('STATE_')[1]
    return state

def get_pool_statistics(api, pool):
    statistics = api.GlobalLB.Pool.get_statistics([pool])
    return statistics

def get_virtual_server_status(api, virtual_server_name, virtual_server_server):
    virtual_server_id = {'name': virtual_server_name, 'server': virtual_server_server}
    status = api.GlobalLB.VirtualServerV2.get_object_status([virtual_server_id])
    return status

def get_virtual_server_state(api, name, server):
    virtual_server_id = {'name': name, 'server': server}
    state = api.GlobalLB.VirtualServerV2.get_enabled_state([virtual_server_id])
    return state

def get_all_virtual_servers(api):
    virtual_servers = api.GlobalLB.VirtualServerV2.get_list()
    return virtual_servers

def get_virtual_server(api, pool):
    virtual_server_list = api.GlobalLB.Pool.get_member_v2([pool])
    # assert there is only 1 result?
    # HACK !!! method returns list instead of dict
    for x in virtual_server_list:
        for y in x:
            virtual_server = {}
            virtual_server = y
    return virtual_server

def get_wide_ip_lb_method(api, wide_ip):
    lb_method = api.GlobalLB.WideIP.get_lb_method(wide_ips=[wide_ip])[0]
    lb_method = lb_method.strip().replace('LB_METHOD_', '').lower()
    return lb_method

def get_wide_ip_pools(api, wide_ip):
    try:
        return api.GlobalLB.WideIP.get_wideip_pool([wide_ip])
    except Exception, e:
        print e

def get_all_wide_ips(api):
    try:
        wide_ips = api.GlobalLB.WideIP.get_list()
        return wide_ips
    except Exception, e:
        print e

def wide_ip_exists(api, wide_ip):
    # hack to determine if wide_ip exists
    result = False
    try:
        api.GlobalLB.WideIP.get_object_status(wide_ips=[wide_ip])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def pool_exists(api, pool):
    # hack to determine if pool exists
    result = False
    try:
        api.GlobalLB.Pool.get_object_status(pool_names=[pool])
        result = True
    except bigsuds.OperationFailed, e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result

def main():
    valid_includes = ['pool', 'wide_ip', 'virtual_server']

    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True),
            include = dict(type='list', required=True),
            pool = dict(type='str', default=None),
            partition = dict(type='str', default='Common'),
            wide_ip = dict(type='str', default=None),
            virtual_server_name = dict(type='str', default=None),
            virtual_server_server = dict(type='str', default=None)
        ),
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    partition = module.params['partition']
    pool = module.params['pool']
    wide_ip = module.params['wide_ip']
    virtual_server_name = module.params['virtual_server_name']
    virtual_server_server = module.params['virtual_server_server']

    include = map(lambda x: x.lower(), module.params['include'])

    include_test = map(lambda x: x in valid_includes, include)
    if not all(include_test):
        module.fail_json(msg="value of include must be one or more of: %s, got: %s" % (",".join(valid_includes), ",".join(include)))

    try:
        api = bigip_api(server, user, password)
        facts = {}

        if pool is not None:
            if not pool_exists(api, pool):
                module.fail_json(msg="pool %s does not exist" % pool)
        if wide_ip is not None:
            if not wide_ip_exists(api, wide_ip):
                module.fail_json(msg="wide ip %s does not exist" % wide_ip)

        if len(include) > 0:
            if 'pool' in include:
                if pool is not None:
                    facts['state'] = get_pool_member_state(api, pool)
                    facts['statistics'] = get_pool_statistics(api, pool)
                    facts['status'] = get_pool_status(api, pool)
                else:
                    facts['pools'] = get_all_pools(api)
            if 'wide_ip' in include:
                if wide_ip is not None:
                    facts['lb_method'] = get_wide_ip_lb_method(api, wide_ip)
                    facts['pools'] = get_wide_ip_pools(api, wide_ip)
                else:
                    facts['wide_ips'] = get_all_wide_ips(api)
            if 'virtual_server' in include:
                if pool is not None:
                    # Look up virtual server given pool if name, server are not provided
                    facts['virtual_server'] = get_virtual_server(api, pool)
                elif virtual_server_name is not None and virtual_server_server is not None:
                    facts['status'] = get_virtual_server_status(api, virtual_server_name, virtual_server_server)
                else:
                    facts['virtual_servers'] = get_all_virtual_servers(api)

            # result = {'ansible_facts': facts}
            result = facts

    except Exception, e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
