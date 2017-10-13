# Lambda port availability check

Lambda function to check specific tcp/ip port availability , and report on it

Optionally, it can record metrics to CloudWatch.

## Inputs

All inputs are either defined as environment variables or as part of event data. Event data
will take priority over environment variables

`HOSTNAME` - url to be checked

`PORT` - http method to use, defaults to `GET`

`TIMEOUT` - timeout when connecting in seconds, defaults to 120s

`REPORT_AS_CW_METRICS` - set to 1 if you wish to store reported data as CW
custom metrics, 0 otherwise, defaults to 1

`CW_METRICS_NAMESPACE` - if CW custom metrics are being reported, this will determine
their namespace, defaults to 'TcpPortCheck'

## Outputs

By default, following properties will be rendered in output Json

`Available` - 0 or 1

`TimeTaken` - Time in ms it took to get response from remote server. Default timeout
is 2 minutes for http requests.

## Dependencies

Lambda function is having no external dependencies by design, so no additional packaging steps are required
for deploying it, such as doing `pip install [libname]`

## CloudWatch Metrics

In order to get some metrics which you can alert on, `REPORT_AS_CW_METRICS` and `CW_METRICS_NAMESPACE` environment
variables are used. Following metrics will be reported

- `Available` - 0 or 1, whether response was received in timely manner, indicating problems with network, DNS lookup or
server timeout

- `TimeTaken` - Time taken to fetch response, reported in milliseconds


## Deployment

You can either deploy Lambda manually, or through [serverless](serverless.com) project.
If serverless is being chosen as method of deployments use command below, while
making sure that you have setup proper access keys. For more information [read here](https://serverless.com/framework/docs/providers/aws/guide/workflow/)

Serverless framework version used during development
is `1.23.0`, but it is very likely that later versions
will function as well

```
sls deploy
```

If you are setting up your Lambda function by hand, make sure it has proper IAM
permissions to push Cloud Watch metrics data, and to write to CloudWatch logs

## Testing

To test function locally with simple Google url (default), run following

```bash
sls invoke local  -f portcheck
```

For more complex example with failed health check, look at test/example.json 

```bash

```


## Schedule execution

Pull requests are welcome to serverless project to deploy CloudWatch rules in order
to schedule execution of Http Checking Lambda function.
