import boto3
from botocore.exceptions import ClientError
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from dateutil import parser
from distutils.util import strtobool
import time

# TODO: Log to file in S3 bucket?
ISACTIVE = os.environ['isActive']

logger = logging.getLogger()
logger.setLevel(logging.INFO)
lam = boto3.client('lambda')

def lambda_handler(event, context):
    current_time = datetime.utcnow()
    logger.info("Running function at " + str(current_time))
    # ADJUST DATE/TIME HERE! SET FOR UTC MONDAY 8AM
    if current_time.weekday() == 0 and current_time.hour == 8:
        # Begin spinup cycle
        logger.info("Attempting spinup cycle")
        wake_tagged('STAGE_1_TAG')
        time.sleep(120) # 2-min wait for systems to come up
        wake_tagged('STAGE_2_TAG')
        time.sleep(120)
        wake_stopped()
    # ADJUST DATE/TIME HERE! SET FOR UTC FRIDAY 11PM
    elif current_time.weekday() == 4 and current_time.hour == 23:
        # Stop running instances
        logger.info("Attempting shutdown")
        stop_tagged_instances()

def stop_tagged_instances():
    for r in get_regions():
        to_sleep = find_tagged_instances('WEEKEND_SLEEP', r)
        for instance in to_sleep:
            sleep_instance(instance, r)

def sleep_instance(instance_id, region):
    ec2 = boto3.resource('ec2', region_name = region)

    if str_to_bool(ISACTIVE) == True:
        try:
            ec2.instances.filter(InstanceIds=[instance_id]).stop()
            logger.info("Stopped " + instance_id + " in " + region)
        except Exception as e:
            logger.info("There was an issue stopping " + instance_id)
            logger.info(e)
    else:
        logger.info("Would have stopped " + instance_id + " in " + region)

def wake_tagged(key):
    for r in get_regions():
        to_wake = find_tagged_instances(key, r)
        for instance in to_wake:
            wake_instance(instance, r)

def wake_stopped():
    for r in get_regions():
        to_wake = find_stopped_instances(r)
        for instance in to_wake:
            wake_instance(instance, r)

def wake_instance(instance_id, region):
    ec2 = boto3.resource('ec2', region_name = region)

    if str_to_bool(ISACTIVE) == True:
        try:
            ec2.instances.filter(InstanceIds=[instance_id]).start()
            logger.info("Started " + instance_id + " in " + region)
        except Exception as e:
            logger.info("There was an issue starting " + instance_id)
            logger.info(e)
    else:
        logger.info("Would have started " + instance_id + " in " + region)

def find_tagged_instances(key, region):
    # Checks instances in a region for a certain tag
    ec2 = boto3.resource('ec2', region_name = region)
    instances = ec2.instances.all()
    found_list = []
    for instance in instances:
        if instance.tags:
            for tag in instance.tags:
                # Has the key we are looking for
                if tag['Key'].upper() == key.upper():
                    found_list.append(instance.id)

    logger.info("Found " + str(len(found_list)) + " ec2 instances in " + region + " tagged " + str(key))
    return found_list

def find_stopped_instances(region):
    # Only looks for instances that are stopped. This is to finish the ordered
    # spin-up process
    ec2 = boto3.resource('ec2', region_name = region)
    instances = ec2.instances.all()
    found_list = []
    for instance in instances:
        if instance.tags:
            for tag in instance.tags:
                # Is stopped, and is a machine we are handling
                if instance.state['Code'] == 80 and tag['Key'].upper() == 'WEEKEND_SLEEP':
                    found_list.append(instance.id)

    logger.info("Found " + str(len(found_list)) + " ec2 instances in " + region + " that were stopped")
    return found_list

def get_regions():
    # Returns a list of all AWS regions
    c = boto3.client('ec2')
    regions = [region['RegionName'] for region in c.describe_regions()['Regions']]
    return regions

def str_to_bool(string):
    return bool(strtobool(str(string)))
