import json
import boto3
import time

def create_alarm(AlarmName,ComparisonOperator,MetricName,Namespace,DatapointsToAlarm,Period,Statistic,Threshold,AlarmDescription,snsTopic,instanceid):
    # Create CloudWatch client
    cloudwatch = boto3.client('cloudwatch')
    # Create alarm
    cloudwatch.put_metric_alarm(
        AlarmName=AlarmName,
        ComparisonOperator=ComparisonOperator,
        MetricName=MetricName,
        Namespace=Namespace,
        DatapointsToAlarm=DatapointsToAlarm,
        Period=Period,
        Statistic=Statistic,
        Threshold=Threshold,
        ActionsEnabled=True,
        AlarmDescription=AlarmDescription,
        AlarmActions=[
                snsTopic,
                ],
        Dimensions=[
        {
          'Name': 'InstanceId',
          'Value': instanceid
        },
    ],
        EvaluationPeriods=1)

AlarmName ="testagent"
ComparisonOperator='GreaterThanThreshold'
MetricName="disk_used_percent"
Namespace='CWAgent'
DatapointsToAlarm=1
Period=300
Statistic='Average'
Threshold=90
AlarmDescription='Alarm when user enters 5 wrong password within 15 minutes'
snsTopic='arn:aws:sns:eu-west-2:184261415726:test'
instanceid='i-0a4e3375ff8b71691'

create_alarm(AlarmName,ComparisonOperator,MetricName,Namespace,DatapointsToAlarm,Period,Statistic,Threshold,AlarmDescription,snsTopic,instanceid)


# Namespace='CWAgent'
# MetricName="mem_used_percent"
# MetricName="disk_used_percent"

# Namespace='AWS/EC2'
# MetricName="CPUUtilization"