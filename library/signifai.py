#!/usr/bin/python

import hmac
import json
import time
import hashlib
import sys

from ansible.module_utils.basic import *
import ansible.module_utils.urls as ansible_url_utils

type2uri = {
    "deployment": "v1/deployments",
    "incident": "v1/incidents",
    "metric": "v1/metrics"
}

value_enums = {
    "incident": ["critical", "high", "medium", "low"],
    "deployment": ["started", "finished-with-errors", "finished-successfully", "error", "rolledback"]
}

required_attrs_by_type = {
    "incident": ["event_description"],
    "deployment": ["event_description"],
    "metric": ["metric_description"]
}
def main(argv=sys.argv):
    argument_spec = dict(
        # Metric contents
        event_type = dict(required=True, choices=type2uri.keys()),
        event_description = dict(required=False),
        metric_description = dict(required=False),
        name = dict(required=False),
        generated_by = dict(required=False, default="ansible"),
        attributes = dict(required=False, type='dict', default={}),
        value = dict(required=True, type='raw'),
        # One of these are required
        application = dict(required=False, default=""),
        service = dict(required=False, default=""),
        host = dict(required=False, default=""),
        # Transport options
        customer_id = dict(required=True, type='int'),
        secret = dict(required=True),
        collectors_host = dict(required=False, default="cadence-in.signifai.io")
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        check_invalid_arguments=True,
        add_file_common_args=False,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False)

    if not module.params['application'] and not module.params['service'] and not module.params['host']:
        module.fail_json(msg="Must provide at least one of 'application', 'service' or 'host' parameters")

    customer_id = module.params['customer_id']
    uri = type2uri[module.params['event_type']]

    if (module.params['event_type'] in value_enums and
        module.params['value'] not in value_enums[module.params['event_type']]):
        module.fail_json(msg="For event_type {0} value must be one of {1}".format(
            module.params['event_type'],
            str.join(", ", value_enums[module.params['event_type']])))

    if (module.params['event_type'] in required_attrs_by_type):
        for attr in required_attrs_by_type[module.params['event_type']]:
            if not module.params[attr]:
                module.fail_json(msg="Events of type {0} must provide {1} attributes".format(
                    module.params['event_type'],
                    str.join(", ", required_attrs_by_type[module.params['event_type']])))

    # Remove the transport parameters
    TRANSPORT_PARAMS = ('customer_id', 'secret', 'collectors_host', 'event_type')
    postbody = dict([(key,val) for key,val in module.params.iteritems() if key not in TRANSPORT_PARAMS and val])

    # Prepare the request
    url = "https://{0}/{1}".format(module.params['collectors_host'], uri)

    signifai_date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    signifai_signstr = str.join(":", ["POST", str(customer_id), "", "application/json", signifai_date])
    signifai_signature = hmac.new(module.params['secret'], signifai_signstr, digestmod=hashlib.sha256).hexdigest()

    body = json.dumps(postbody)

    headers = {
        "Authorization": "signifai {0}:{1}".format(module.params['customer_id'], signifai_signature),
        "X-Signifai-Date": signifai_date,
        "Content-Type": "application/json"
    }

    # Submit the request
    resp, info = ansible_url_utils.fetch_url(module, url, data=body, headers=headers, method='POST', timeout=30)
    if resp is None:
        module.fail_json(msg="Request failed: {0}".format(info['msg']), err_json=body, http_info=info, http_resp=resp)

    status_code = int(info['status'])

    # Pass/fail
    if status_code != 200:
        module.fail_json(msg="Failed submitting event to signifai: {0}".format(info['msg']), err_json=body)
    else:
        module.exit_json(changed=True)


if __name__ == "__main__":
    sys.exit(main())
