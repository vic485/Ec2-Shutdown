# Ec2-Shutdown
Small AWS Lambda function to start and stop EC2 instances at defined date/times. Created to help the company I worked for save money but stopping instances on Friday nights, and restarting them automatically on Monday morning. The function also has a staged startup system to spin up instances in a proper-ish order.

# Setting up
Create an IAM role for the function, with the permissions in the `permissions.json` file.

Put the function.py code in a Python 3 lambda function. Add a environment variable called `isActive` and set it to either `True` or `False`. The function can be triggered with a cron job, and the times in the function should be adjusted as necessary to fit with the cron job. Times are in UTC for both.

Instances to be affected by this function need a tag with the name `WEEKEND_SLEEP` by default. Additional tags can be set and added to the function for a staged spin-up system.
