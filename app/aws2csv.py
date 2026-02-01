#!/usr/bin/env python3
import json, csv
from os import environ,path
from shutil import copyfile
from typing import List, Dict, Iterable, Optional, Any, Union
from pprint import pprint
from argparse import ArgumentParser,RawTextHelpFormatter
from tqdm import tqdm

# 自作クラスを呼び出し
from my_classes import AwsData


def get_headers():
    
    return {
        'ec2_instances':[
            'インスタンス名','インスタンスID','インスタンスタイプ','ステータス','起動時間'
        ],
        'rds_instances':[
            'DBインスタンス名','DBインスタンスID','DBインスタンスタイプ','ステータス','起動時間'
        ],
        'sewcurity_groups':[
            'セキュリティグループ名','セキュリティグループID','VPCID','Description'
        ],
        'load_balancers':[
            'ロードバランサー名','ロードバランサーID','VPCID','タイプ','Description'
        ],
        'load_balancer_listeners':[
            'ロードバランサー名','リスナー名','リスナーポート','優','タイプ','Description'
        ],
        'load_balancer_listeners':[
            'ロードバランサー名','ロードバランサーID','VPCID','タイプ','Description'
        ],

    }

def get_defaults(key: str = False):
    defaults = {
        'profile_name': ('default'
            if not environ.get('AWS_PROFILE') 
                else environ.get('AWS_PROFILE')),
        'region_name': ('us-east-1'
            if environ.get('AWS_REGION') is None
                else environ.get('AWS_REGION')),
        'file_path': ('./data/aws2csv.json'
            if not environ.get('AWS2CSV_DATA_FILE')
                else environ.get('AWS2CSV_DATA_FILE')),
        'data_dir': ('./data'
            if not environ.get('AWS2CSV_DATA_DIR')
                else environ.get('AWS2CSV_DATA_DIR')),
        'debug': (False
            if not environ.get('AWS2CSV_DEBUG')
                else environ.get('AWS2CSV_DEBUG'),False),
        'skip_s3_usage': (False
            if not environ.get('AWS2CSV_SKIP_S3_USAGE')
                else environ.get('AWS2CSV_SKIP_S3_USAGE'),False),
        'over_write': (False
            if not environ.get('AWS2CSV_OVER_WRITE')
                else environ.get('AWS2CSV_OVER_WRITE'),False),
    }
    return defaults[key] if key in defaults else defaults

def get_help(key: str = False):
    help = {
        'command':      (f'実行するコマンド\n'+
        f'  scan: 環境データを取得する\n'+
        f'  export: 環境データをCSVファイルに出力する'),
        'description':   'AWS環境データをCSVファイル出力するスクリプトです。',
        'profile_name':  f'データ取得対象のAWSプロファイル名\n'+
        f'  デフォルト: {get_defaults("profile_name")}',
        'region_name':   f'データ取得対象のAWSリージョン\n'+
        f'  デフォルト: {get_defaults("region_name")}',
        'debug':         f'デバッグモード\n'+
        f'  デフォルト: 無効',
        'skip_s3_usage': f'S3バケットの使用量スキャンをスキップ\n'+
        f'  デフォルト: 無効',
        'file_path':     f'環境データの保存先ファイルパス\n'+
        f'  デフォルト: {get_defaults("file_path")}',
        'data_dir':      f'環境データ・CSVファイルの保存先ディレクトリ\n'+
        f'  デフォルト: {get_defaults("data_dir")}',
        'over_write':    f'環境データファイルを上書きする\n'+
        f'  デフォルト: 無効',
    }
    return help[key] if key in help else help

def check_data_file(file_path: str) -> bool:
    return path.exists(file_path)

def check_data_dir(data_dir: str) -> bool:
    return path.exists(data_dir)


# コマンドライン引数をパース
def parse_args():
    commands = ['scan','export']
    parser=ArgumentParser(formatter_class=RawTextHelpFormatter,description=get_help('description'))
    parser.add_argument('command', type=str, choices=commands, help=get_help('command'))
    parser.add_argument('--profile', '-p', type=str, default=get_defaults('profile_name'), help=get_help('profile_name'))
    parser.add_argument('--region', '-r', type=str, default=get_defaults('region_name'), help=get_help('region_name'))
    parser.add_argument('--file_path', '-f', type=str, default=get_defaults('file_path'), help=get_help('file_path'))
    parser.add_argument('--data_dir', '-d', type=str, default=get_defaults('data_dir'), help=get_help('data_dir'))
    parser.add_argument('--debug', action='store_false', default=get_defaults('debug'), help=get_help('debug'))
    parser.add_argument('--over-write','-w', action='store_true', default=get_defaults('over_write'), help=get_help('over_write'))
    parser.add_argument('--skip_s3_usage', '-s', action='store_false', default=get_defaults('skip_s3_usage'), help=get_help('skip_s3_usage'))
    return parser.parse_args()


def main():
    args=parse_args()
    if args.command == 'scan':
        scan_aws(
            args.profile, 
            args.region, 
            args.file_path,
            args.over_write,
            args.debug)
    elif args.command == 'export':
        export_aws(args.file_path)
    return True

# 環境データを取得
def scan_aws(profile_name: str, region_name: str,
     file_path: str=get_defaults('file_path'),
     over_write: bool=get_defaults('over_write'),debug: bool=get_defaults('debug')) -> AwsData:
    if (over_write is True) and check_data_file(file_path) is True:
        print(f'環境データファイル`{file_path}`が存在します。環境データを上書きします。元のファイルを{file_path}.bakに保存します。')
        copyfile(file_path, file_path + '.bak')
    else:
       print(f'環境データを{file_path}に保存しました。')
    aws_data = AwsData(profile_name=profile_name, region_name=region_name,scan=True,debug=debug)
    aws_data._save_data(aws_data.as_dict(), file_path)
    return aws_data

# 環境データをCSVファイルに出力
def export_aws(file_path: str=get_defaults('file_path')) -> None:
    print(f'export_aws(): file_path->{file_path}')
    if check_data_file(file_path) is True:
        print(f'環境データファイル`{file_path}`から環境データを読み込みます。')
        aws_data = AwsData(data_file=file_path)
    print(f'環境データをCSVファイルに出力します。')
    if not isinstance(aws_data, AwsData):
        print(f'環境データの読み込みに失敗しました。')
        return False
    else:
        pass
    return True

if __name__ == '__main__':
    main()