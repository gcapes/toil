# Copyright (C) 2015-2021 Regents of the University of California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

from typing import Optional
from toil.lib.misc import printq
from toil.lib.retry import retry
from toil.lib.aws.credentials import client, resource

try:
    from boto.exception import BotoServerError
except ImportError:
    BotoServerError = None  # AWS/boto extra is not installed

logger = logging.getLogger(__name__)


@retry(errors=[BotoServerError])
def delete_iam_role(role_name: str, region: Optional[str] = None, quiet: bool = True):
    from boto.iam.connection import IAMConnection
    iam_client = client('iam', region_name=region)
    iam_resource = resource('iam', region_name=region)
    boto_iam_connection = IAMConnection()
    role = iam_resource.Role(role_name)
    # normal policies
    for attached_policy in role.attached_policies.all():
        printq(f'Now dissociating policy: {attached_policy.name} from role {role.name}', quiet)
        role.detach_policy(PolicyName=attached_policy.name)
    # inline policies
    for attached_policy in role.policies.all():
        printq(f'Deleting inline policy: {attached_policy.name} from role {role.name}', quiet)
        # couldn't find an easy way to remove inline policies with boto3; use boto
        boto_iam_connection.delete_role_policy(role.name, attached_policy.name)
    iam_client.delete_role(RoleName=role_name)
    printq(f'Role {role_name} successfully deleted.', quiet)


@retry(errors=[BotoServerError])
def delete_iam_instance_profile(instance_profile_name: str, region: Optional[str] = None, quiet: bool = True):
    iam_resource = resource('iam', region_name=region)
    instance_profile = iam_resource.InstanceProfile(instance_profile_name)
    for role in instance_profile.roles:
        printq(f'Now dissociating role: {role.name} from instance profile {instance_profile_name}', quiet)
        instance_profile.remove_role(RoleName=role.name)
    instance_profile.delete()
    printq(f'Instance profile "{instance_profile_name}" successfully deleted.', quiet)


@retry(errors=[BotoServerError])
def delete_sdb_domain(sdb_domain_name: str, region: Optional[str] = None, quiet: bool = True):
    sdb_client = client('sdb', region_name=region)
    sdb_client.delete_domain(DomainName=sdb_domain_name)
    printq(f'SBD Domain: "{sdb_domain_name}" successfully deleted.', quiet)


@retry(errors=[BotoServerError])
def delete_s3_bucket(bucket: str, region: Optional[str], quiet: bool = True):
    printq(f'Deleting s3 bucket in region "{region}": {bucket}', quiet)
    s3_client = client('s3', region_name=region)
    s3_resource = resource('s3', region_name=region)

    paginator = s3_client.get_paginator('list_object_versions')
    for response in paginator.paginate(Bucket=bucket):
        versions = response.get('Versions', []) + response.get('DeleteMarkers', [])
        for version in versions:
            printq(f"    Deleting {version['Key']} version {version['VersionId']}", quiet)
            s3_client.delete_object(Bucket=bucket, Key=version['Key'], VersionId=version['VersionId'])
    s3_resource.Bucket(bucket).delete()
    printq(f'\n * Deleted s3 bucket successfully: {bucket}\n\n', quiet)
