import json
import os
import boto3
from time import perf_counter as pc
import socket


class Config:
    """Lambda function runtime configuration"""

    HOSTNAME = 'HOSTNAME'
    PORT = 'PORT'
    TIMEOUT = 'TIMEOUT'
    REPORT_AS_CW_METRICS = 'REPORT_AS_CW_METRICS'
    CW_METRICS_NAMESPACE = 'CW_METRICS_NAMESPACE'

    def __init__(self, event):
        self.event = event
        self.defaults = {
            self.HOSTNAME: 'google.com.au',
            self.PORT: 443,
            self.TIMEOUT: 120,
            self.REPORT_AS_CW_METRICS: '1',
            self.CW_METRICS_NAMESPACE: 'TcpPortCheck',
        }

    def __get_property(self, property_name):
        if property_name in self.event:
            return self.event[property_name]
        if property_name in os.environ:
            return os.environ[property_name]
        if property_name in self.defaults:
            return self.defaults[property_name]
        return None

    @property
    def hostname(self):
        return self.__get_property(self.HOSTNAME)

    @property
    def port(self):
        return self.__get_property(self.PORT)

    @property
    def timeout(self):
        return self.__get_property(self.TIMEOUT)

    @property
    def reportbody(self):
        return self.__get_property(self.REPORT_RESPONSE_BODY)

    @property
    def cwoptions(self):
        return {
            'enabled': self.__get_property(self.REPORT_AS_CW_METRICS),
            'namespace': self.__get_property(self.CW_METRICS_NAMESPACE),
        }


class PortCheck:
    """Execution of HTTP(s) request"""

    def __init__(self, config):
        self.config = config

    def execute(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(int(self.config.timeout))
        try:
            # start the stopwatch
            t0 = pc()

            connect_result = sock.connect_ex((self.config.hostname, int(self.config.port)))
            if connect_result == 0:
                available = '1'
            else:
                available = '0'

            # stop the stopwatch
            t1 = pc()

            result = {
                'TimeTaken': int((t1 - t0) * 1000),
                'Available': available
            }
            print(f"Socket connect result: {connect_result}")
            # return structure with data
            return result
        except Exception as e:
            print(f"Failed to connect to {self.config.hostname}:{self.config.port}\n{e}")
            return {'Available': 0, 'Reason': str(e)}


class ResultReporter:
    """Reporting results to CloudWatch"""

    def __init__(self, config):
        self.config = config
        self.options = config.cwoptions

    def report(self, result):
        if self.options['enabled'] == '1':
            try:
                endpoint = f"{self.config.hostname}:{self.config.port}"
                cloudwatch = boto3.client('cloudwatch')
                metric_data = [{
                    'MetricName': 'Available',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint}
                    ],
                    'Unit': 'None',
                    'Value': int(result['Available'])
                }]
                if result['Available'] == '1':
                    metric_data.append({
                        'MetricName': 'TimeTaken',
                        'Dimensions': [
                            {'Name': 'Endpoint', 'Value': endpoint}
                        ],
                        'Unit': 'Milliseconds',
                        'Value': int(result['TimeTaken'])
                    })

                result = cloudwatch.put_metric_data(
                    MetricData=metric_data,
                    Namespace=self.config.cwoptions['namespace']
                )
                
                print(f"Sent data to CloudWatch requestId=:{result['ResponseMetadata']['RequestId']}")
            except Exception as e:
                print(f"Failed to publish metrics to CloudWatch:{e}")


def lambda_handler(event, context):
    """Lambda function handler"""

    config = Config(event)
    port_check = PortCheck(config)

    result = port_check.execute()

    # report results
    ResultReporter(config).report(result)

    result_json = json.dumps(result, indent=4)
    # log results
    print(f"Result of checking  {config.hostname}:{config.port}\n{result_json}")

    # return to caller
    return result
