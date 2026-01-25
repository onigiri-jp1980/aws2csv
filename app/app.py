import json, csv
from os import environ,path
from boto3.session import Session
from typing import List, Dict
from pprint import pprint
from argparse import ArgumentParser,RawTextHelpFormatter

def parse_args():
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('--profile', type=str, default='default', help='AWS profile name')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region name')
    parser.add_argument('--service', type=str, default='ec2', help='AWS service name')
    return parser.parse_args()


def get_ec2_client(
    profile_name: str='default',
    region_name: str='us-east-1')->boto3.client.EC2:
    session = Session(profile_name=profile_name)
    return session.client('ec2', region_name=region_name)

def get_ec2_instances(client: boto3.client.EC2) -> List[Dict]:
    response = client.describe_instances()
    return [i for r in response['Reservations'] for i in r['Instances']]

def build_ec2_instances_csv(data: List[Dict]) -> str:
    csv_data=[]
    for instance in data:
        instance_name=next((t['Value'] for t in instance['Tags'] if t['Key'] == 'Name'), '')
        csv_data.append([
            instance_name,
            instance['InstanceId'],
            instance['InstanceType'],
            instance['State']['Name'],
            instance['LaunchTime'],
        ])
    return csv_data

def main():
    args=parse_args()
    hearders=[
        'インスタンス名','インスタンスID','インスタンスタイプ','ステータス','起動時間'
    ]
    ec2=get_ec2_client(profile_name=args.profile,region_name=args.region)
    if not path.exists('ec2_instances.json'):
        print('ec2_instances.json not found')
        data=build_ec2_instances_csv(get_ec2_instances(ec2))
    else:
        print('ec2_instances.json exists.')
        with open('ec2_instances.json', 'r') as f:
            data=json.load(f)
    with open('ec2_instances.csv', 'w') as f:
        writer=csv.writer(f)
        writer.writerow(hearders)
        writer.writerows(build_ec2_instances_csv(data),)
    return

if __name__ == '__main__':
    main()