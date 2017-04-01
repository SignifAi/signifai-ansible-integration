# signifai-rest-notification-role
Ansible module for notifying SignifAI REST API of a metric/deployment/incident from within a playbook.
Mostly used to report on deployment events.  

## Including in your playbooks

Copy this whole directory (minus test-pb.yml) into the `roles/signifai` subdirectory starting
from the directory of your playbook. 

`mkdir -p roles/signifai && cp -R signifai-ansible-integration/* roles/signifai/ && rm roles/signifai/test-pb.yml`

Within your playbook, before the `tasks` section, put a line like this:

```yaml
  roles:
    - signifai
```

See test-pb.yml for a detailed example of usage. 

## Syntax

Mostly just like the REST API. 

| Attribute                | Value/Type                            | Required                         | Description                                |
| ------------------------ | ------------------------------------  | :------------------------------: | ------------------------------------------ |
| event_type               | 'incident', 'deployment', 'metric'    | Y                                | Type of event.                             |
| event_description        | String                                | Y ('incident' or 'deployment')   | Description of event.                      |
| metric_description       | String                                | Y (only for 'metrics')           | Description of metric.                     |
| name                     | String                                | N                                | Name of event, incident, metric            |
| event_source             | String                                | Y                                | App/object generating the event.           |
| attributes               | Dictionary                            | N                                | Additional attributes.[1]                  |
| value (for 'metric')     | (Inferred from value/schema)          | Y                                | Metric's value                             |
| value (for 'incident')   | 'critical', 'high', 'medium', 'low'   | Y                                | The priority/status of the incident.       |
| value (for 'deployment') | 'started', 'finished-with-errors', 'finished-successfully', 'error', 'rolledback' | Y | Deployment's current state.   |
| application              | String                                | If no 'service' or 'host'        | The application the event applies to.      |
| service                  | String                                | If no 'application' or 'host'    | The service the event applies to.          |
| host                     | String                                | If no 'service' or 'application' | The host the event applies to.             |
| jwt_token                | String                                | Y                                | Your customer jwt token (from registration)|
| collectors_host          | String                                | N                                | Alternate collector hostname to report to  | 

You can specify 'application', 'service' and 'host' at the same time, but you must specify at least one. 

The 'metric' value is implied by its type as specified in your parameter and/or by our schema.
