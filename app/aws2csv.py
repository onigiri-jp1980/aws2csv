#! /usr/bin/env python3
from os import environ,path
import json,csv
from boto3.session import Session
from botocore.paginate import Paginator
from argparse import ArgumentParser,RawTextHelpFormatter,Namespace


class Defaults:
    profile:str = 'default' if 'AWS_PROFILE' not in environ else environ['AWS_PROFILE']
    region:str = 'us-east-1' if 'AWS_REGION' not in environ else environ['AWS_REGION']
    service:str = 'ec2' if 'AWS2CSV_SERVICE' not in environ else environ['AWS2CSV_SERVICE']
    output_json:str = 'aws2csv.json' if 'AWS2CSV_OUTPUT_JSON' not in environ else environ['AWS2CSV_OUTPUT_JSON']
    output_csv:str = 'aws2csv.csv' if 'AWS2CSV_OUTPUT_CSV' not in environ else environ['AWS2CSV_OUTPUT_CSV']
    file:str = 'aws2csv.json' if 'AWS2CSV_INFO_FILE' not in environ else environ['AWS2CSV_INFO_FILE']
    help : dict
    command: dict
    serices: dict
    def __init__(self):
        self.help = {
            'profile':     f'AWS プロファイル名 デフォルト値:{self.profile}(AWS_PROFILE)',
            'region':      f'AWS リージョン デフォルト値:{self.region}(AWS_REGION)',
            'service':     f'AWS サービス名 デフォルト値:{self.service}(AWS2CSV_SERVICE)',
            'output_json': f'JSON出力ファイル名 デフォルト値:{self.output_json}(AWS2CSV_OUTPUT_JSON)',
            'output_csv':  f'CSV出力ファイル名 デフォルト値:{self.output_csv}(AWS2CSV_OUTPUT_CSV)',
            'file':        f'情報ファイル名 デフォルト値:{self.file}(AWS2CSV_INFO_FILE)',
        }
        self.command = {
            'export':  '情報を出力する',
            'inspect': 'AWS環境から情報を取得する',
        }
        self.serices = {
            'ec2': {
                'client': 'ec2', #利用するサービスクライアント名
                'output': 'ec2.json', #出力ファイル名
                'help': 'EC2の情報を取得する', #ヘルプメッセージ
            },
            'rds': {
                'client': 'rds',
                'output': 'rds_instances.json',
                'help': 'RDSインスタンスの情報を取得する',
            },
                            'load_balancer': {
                'client': 'elbv2',
                'output': 'load_balancer.json',
                'help': 'ロードバランサーの情報を取得する',
            },

            # EC2のサービスクライアントで取得するもの
            'vpc': {
                'client': 'ec2', 
                'output': 'vpc.json',
                'help': 'VPCの情報を取得する',
            },
            'security_group': {
                'client': 'ec2', 
                'output': 'security_group_rules.json',
                'help': 'セキュリティグループの情報を取得する',
            },
        }
    # ヘルプメッセージを取得する
    def get_help(self,key:str)->str:
        return self.help[key]

defaults = Defaults()
basename=path.basename(__file__)


class AWSClient:
    def __init__(self,profile:str,region:str):
        self._session=Session(profile_name=profile,region_name=region)

    class EC2:
        def __init__(self,session:Session):
            self._client=super()._session.client('ec2')
            self._instances=[]
            self._paginator=self._client.get_paginator('describe_instances')

        def get_instances(self,paginator: Paginator):
            for page in paginator.paginate():
                reservations= page['Reservations']
                self._instances.extend([i for r in reservations for i in r['Instances']])
            return self._instances

# 引数を解析する
def parse_args():
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('--profile', type=str, default=defaults.profile, help=defaults.get_help('profile'))
    parser.add_argument('--region', type=str, default=defaults.region, help=defaults.get_help('region'))
    parser.add_argument('--service', type=str, default=defaults.service, help=defaults.get_help('service'))
    parser.add_argument('--output_json', type=str, default=defaults.output_json, help=defaults.get_help('output_json'))
    parser.add_argument('--output_csv', type=str, default=defaults.output_csv, help=defaults.get_help('output_csv'))
    parser.add_argument('--file', type=str, default=defaults.file, help=defaults.get_help('file'))
    return parser.parse_args()


def main():
    args=parse_args()
    print(f"{basename}: got args->{args}")

def inspect_aws

if __name__ == "__main__":
    main()