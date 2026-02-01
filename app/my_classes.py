from boto3.session import Session
from boto3 import client as boto3_client
from typing import List, Dict, Iterable, Optional, Any, Union
from os import environ
import json
from tqdm import tqdm

class AwsData:
    _skip_s3_usage: bool = False
    _debug: bool = False
    ec2: list[Dict] = []
    rds: list[Dict] = []
    vpc: list[Dict] = []
    s3: list[Dict] = []
    security_groups: Dict = {"groups":[], "rules":[]}
    load_balancer: Dict = {
        "load_balancers":[], 
        "rules":[], 
        "listeners":[],
        "target_groups":[]}
    # AWSクライアントをまとめるサブクラス
    class clients:
        ec2: boto3_client.EC2
        rds: boto3_client.RDS
        load_balancer: boto3_client.ELBv2
        s3: boto3_client.S3
    # コンストラクタ
    def __init__(self,
        profile_name: str='default' if not environ.get('AWS_PROFILE') else environ.get('AWS_PROFILE'),
        region_name: str='us-east-1' if environ.get('AWS_REGION') is None else environ.get('AWS_REGION'),
        debug: bool=False,
        scan: bool=False,
        data_file: str=None,
        skip_s3_usage: bool=False):
        self._debug = debug
        self._skip_s3_usage = skip_s3_usage
        self._session = Session(profile_name=profile_name)
        with tqdm(total=4, desc='AWSクライアントを初期化しています') as pbar:
            self.clients.ec2 = self._session.client('ec2')
            pbar.update(1)
            self.clients.rds = self._session.client('rds')
            pbar.update(1)
            self.clients.load_balancer = self._session.client('elbv2')
            pbar.update(1)
            self.clients.s3 = self._session.client('s3')
            pbar.update(1)
        if scan:
            self._scan_aws()
        elif data_file is not None:
            self._load_data(self._load_json(data_file))
        else:
            raise ValueError('data_file または scan のいずれかを指定してください')
    def _scan_aws(self):
        with tqdm(total=8 , desc='AWSの情報を取得しています') as pbar:
            self.ec2 = self.get_ec2_instances()
            pbar.update(1)
            self.rds = self.get_rds_instances()
            pbar.update(1)
            self.vpc = self.get_vpc()
            pbar.update(1)
            self.s3 = self.get_s3()
            pbar.update(1)
        self.security_groups["groups"] = self.get_security_groups()
        self.security_groups["rules"] = self.get_security_group_rules()
        self.load_balancer["load_balancers"] = self.get_load_balancers()
        self.load_balancer["listeners"] = self.get_load_balancer_listeners()
    def _load_data(self, data: Dict=None):
        if data is None:
            return
        self.ec2 = data['ec2']
        self.rds = data['rds']
        self.vpc = data['vpc']
        self.s3 = data['s3']
        self.security_groups["groups"] = data['security_groups']['groups']
        self.security_groups["rules"] = data['security_groups']['rules']
        self.load_balancer["load_balancers"] = data['load_balancer']['load_balancers']
        self.load_balancer["listeners"] = data['load_balancer']['listeners']
        self.load_balancer["target_groups"] = data['load_balancer']['target_groups']
        self.load_balancer["rules"] = data['load_balancer']['rules']

    # VPCを取得
    def get_vpc(self) -> List[Dict]:
        vpc = []
        paginator = self.clients.ec2.get_paginator('describe_vpcs')
        for page in paginator.paginate():
            for vpc_item in page['Vpcs']:
                vpc.append(vpc_item)
        return vpc

    # EC2インスタンスを取得
    def get_ec2_instances(self) -> List[Dict]:
        instances = []
        paginator = self.clients.ec2.get_paginator('describe_instances')
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instances.append(instance)
        return instances

    # RDSインスタンスを取得
    def get_rds_instances(self) -> List[Dict]:
        instances = []
        paginator = self.clients.rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                instances.append(instance)
        return instances

    # セキュリティグループを取得
    def get_security_groups(self) -> List[Dict]:
        security_groups = []
        paginator = self.clients.ec2.get_paginator('describe_security_groups')
        for page in paginator.paginate():
            for security_group in page['SecurityGroups']:
                security_groups.append(security_group)
        return security_groups

    # セキュリティグループルールを取得
    def get_security_group_rules(self) -> List[Dict]:
        rules = []
        paginator = self.clients.ec2.get_paginator('describe_security_group_rules')
        for page in paginator.paginate():
            for rule in page['SecurityGroupRules']:
                rules.append(rule)
        return rules

    # ロードバランサーを取得
    def get_load_balancers(self) -> List[Dict]:
        load_balancers = []
        paginator = self.clients.load_balancer.get_paginator('describe_load_balancers')
        for page in paginator.paginate():
            for load_balancer in page['LoadBalancers']:
                load_balancers.append(load_balancer)
        return load_balancers

    # ロードバランサールールを取得
    def get_load_balancer_rules(self) -> List[Dict]:
        rules = []
        paginator = self.clients.load_balancer.get_paginator('describe_rules')
        for listener in self.load_balancer["listeners"]:
            for l in listener:
                for rule in paginator.paginate(
                    ListenerArn=l['ListenerArn']
                ):
                    rules.append(rule)
        return rules

    # ロードバランサーリスナーを取得
    def get_load_balancer_listeners(self) -> List[Dict]:
        listeners = []
        paginator = self.clients.load_balancer.get_paginator('describe_listeners')
        for load_balancer in self.load_balancer["load_balancers"]:
            for listener in paginator.paginate(
                LoadBalancerArn=load_balancer['LoadBalancerArn']
            ):
                listeners.append(listener['Listeners'])
        return listeners

    # ロードバランサーターゲットグループを取得
    def get_load_balancer_target_groups(self) -> List[Dict]:
        target_groups = []
        paginator = self.clients.load_balancer.get_paginator('describe_target_groups')
        for load_balancer in self.load_balancer["load_balancers"]:
            for target_group in paginator.paginate(
                LoadBalancerArn=load_balancer['LoadBalancerArn']
            ):
                target_groups.append(target_group['TargetGroups'])
        return target_groups

    # ターゲット情報を取得
    def get_target_group_targets(self) -> List[Dict]:
        targets = []
        paginator = self.clients.load_balancer.get_paginator('describe_target_health')
        for target_group in self.load_balancer["target_groups"]:
            for target in paginator.paginate(
                TargetGroupArn=target_group['TargetGroupArn']
            ):
                targets.append(target['Targets'])
        return targets

    def as_dict(self) -> Dict:
        return {
            "vpc": self.vpc,
            "ec2": self.ec2,
            "rds": self.rds,
            "s3": self.s3,
            "security_groups": self.security_groups,
            "load_balancer": self.load_balancer,
        }

    # S3を取得
    def get_s3(self) -> List[Dict]:
        s3 = []
        buckets = self.clients.s3.list_buckets()
        with tqdm(total=len(buckets['Buckets']), desc='S3バケットの情報を取得しています') as pbar:
            for bucket in buckets['Buckets']:
                if not self._skip_s3_usage:
                    bucket['Usage'] = self._get_s3_bucket_usage(bucket)
                pbar.update(1)
                s3.append(bucket)
            return s3

    #オブジェクトサイズを集計
    def _get_s3_bucket_usage(self, bucket: Dict) -> Dict:
        if self._debug:
            print(f'バケット`{bucket["Name"]}`のオブジェクトサイズを集計します')
        objects = []
        paginator = self.clients.s3.get_paginator('list_objects')
        for page in paginator.paginate(
            Bucket=bucket['Name']
        ):
            for object in page.get('Contents', []):
                objects.append(object)
        return sum([object.get('Size', 0) for object in objects])

    def _load_json(self, file_path: str) -> Dict:
        with open(file_path, 'r') as f:
            return json.load(f)

    def _save_data(self, data: Dict=None, file_path: str=None) -> None:
        if file_path is None:
            return False
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4,default=str)
        return True
    def build_ec2_csv(self) -> None:
        pass
    def build_rds_csv(self) -> None:
        pass
    def build_vpc_csv(self) -> None:
        pass
    def build_s3_csv(self) -> None:
        pass
    def build_security_groups_csv(self) -> None:
        pass
    def build_load_balancer_csv(self) -> None:
        pass
    def build_load_balancer_rules_csv(self) -> None:
        pass
    def build_load_balancer_target_groups_csv(self) -> None:
        pass
    def build_load_balancer_target_group_targets_csv(self) -> None:
        pass
    def _perm_to_rows(
        sg: Dict[str, Any],
        direction: str,
        perm: Dict[str, Any],
    ) -> Iterable[Dict[str, str]]:
        """
        direction: "ingress" or "egress"
        """
        ip_proto = str(perm.get("IpProtocol", ""))
        from_port = perm.get("FromPort")
        to_port = perm.get("ToPort")

        # -1 は全プロトコル/全ポート扱い
        if ip_proto == "-1":
            proto = "all"
            port_range = "all"
        else:
            proto = ip_proto
            if from_port is None and to_port is None:
                port_range = ""
            elif from_port == to_port:
                port_range = str(from_port)
            else:
                port_range = f"{from_port}-{to_port}"

        base = {
            "GroupId": sg.get("GroupId", ""),
            "GroupName": sg.get("GroupName", ""),
            "VpcId": sg.get("VpcId", ""),
            "Direction": direction,
            "Protocol": proto,
            "PortRange": port_range,
        }

        # IPv4 CIDR
        for r in perm.get("IpRanges", []):
            cidr = r.get("CidrIp", "")
            desc = r.get("Description", "") or ""
            row = base | {
                "SourceOrDestination": cidr,
                "SourceOrDestinationType": "cidr_ipv4",
                "RuleDescription": desc,
            }
            yield row

        # IPv6 CIDR
        for r in perm.get("Ipv6Ranges", []):
            cidr = r.get("CidrIpv6", "")
            desc = r.get("Description", "") or ""
            row = base | {
                "SourceOrDestination": cidr,
                "SourceOrDestinationType": "cidr_ipv6",
                "RuleDescription": desc,
            }
            yield row

        # 参照SG（同一/他SG）
        for r in perm.get("UserIdGroupPairs", []):
            gid = r.get("GroupId", "")
            uid = r.get("UserId", "")
            desc = r.get("Description", "") or ""
            val = f"{uid}:{gid}" if uid else gid
            row = base | {
                "SourceOrDestination": val,
                "SourceOrDestinationType": "security_group",
                "RuleDescription": desc,
            }
            yield row

        # Prefix List（S3 などのマネージド宛先に出ることがある）
        for r in perm.get("PrefixListIds", []):
            plid = r.get("PrefixListId", "")
            desc = r.get("Description", "") or ""
            row = base | {
                "SourceOrDestination": plid,
                "SourceOrDestinationType": "prefix_list",
                "RuleDescription": desc,
            }
            yield row


def export_sg_rules_csv(region: str, out_path: str, vpc_id: Optional[str] = None) -> None:
    ec2 = boto3.client("ec2", region_name=region)

    filters = []
    if vpc_id:
        filters.append({"Name": "vpc-id", "Values": [vpc_id]})

    paginator = ec2.get_paginator("describe_security_groups")
    fieldnames = [
        "GroupId",
        "GroupName",
        "VpcId",
        "Direction",
        "Protocol",
        "PortRange",
        "SourceOrDestinationType",
        "SourceOrDestination",
        "RuleDescription",
    ]

