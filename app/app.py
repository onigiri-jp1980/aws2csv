import json, csv
from os import environ,path
from boto3.session import Session
from typing import List, Dict
from pprint import pprint
from argparse import ArgumentParser,RawTextHelpFormatter

headers={
    'ec2':[
        'インスタンス名','インスタンスID','インスタンスタイプ','ステータス','起動時間'
    ],
    'rds':[
        'DBインスタンス名','DBインスタンスID','DBインスタンスタイプ','ステータス','起動時間'
    ],
    'sewcurity_group':[
        'セキュリティグループ名','セキュリティグループID','VPCID','Description'
    ]
}


def parse_args():
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('--profile', type=str, default='default', help='AWS profile name')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region name')
    parser.add_argument('--service', type=str, default='ec2', help='AWS service name')
    return parser.parse_args()


def get_ec2_client(
    profile_name: str='default',
    region_name: str='us-east-1',
    service_name: str='ec2')->boto3.client.EC2:
    session = Session(profile_name=profile_name)
    return session.client(service_name, region_name=region_name)

def get_ec2_instances(client: boto3.client.EC2) -> List[Dict]:
    response = client.describe_instances()
    return [i for r in response['Reservations'] for i in r['Instances']]

def build_csv(data: List[Dict],service_name: str) -> str:
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
    service=args.service if args.service != 'security_group' else 'vpc'
    client=get_client(profile_name=args.profile,region_name=args.region,service_name=service)
    data=get_data(client)
    build_csv(data,service)
    return

if __name__ == '__main__':
    main()