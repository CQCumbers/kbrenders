# Run this script using heroku scheduler to process queue
import boto3, os

# Check if messages in queue
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='kbrenders-queue.fifo')
num_messages = int(queue.attributes['ApproximateNumberOfMessages'])
if num_messages > 0:
    # start EC2 instance to process queue (will shut itself down afterwards)
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(os.environ['AWS_INSTANCE_ID'])
    instance.start()
    print('Start signal sent to instance '+os.environ['AWS_INSTANCE_ID'])
    print('Processing '+str(num_messages)+' messages')
