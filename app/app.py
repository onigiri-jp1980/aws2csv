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

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for page in paginator.paginate(Filters=filters):
            for sg in page.get("SecurityGroups", []):
                for perm in sg.get("IpPermissions", []):
                    for row in _perm_to_rows(sg, "ingress", perm):
                        w.writerow(row)
                for perm in sg.get("IpPermissionsEgress", []):
                    for row in _perm_to_rows(sg, "egress", perm):
                        w.writerow(row)



def main():
    args=parse_args()
    service=args.service if args.service != 'security_group' else 'vpc'
    client=get_client(profile_name=args.profile,region_name=args.region,service_name=service)
    data=get_data(client)
    build_csv(data,service)
    return

if __name__ == '__main__':
    main()