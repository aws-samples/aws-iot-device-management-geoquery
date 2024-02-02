# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Find account id
ACCOUNT_ID=`aws sts get-caller-identity --query "Account" --output text`

# Delete FleetMetric
echo "Deleting FleetMetric 'OfflineChargers' "
aws iot delete-fleet-metric --metric-name "OfflineChargers" --region us-east-1                                           

#delete things, certificates, thing group, thing type
bash deleteThing.sh

echo "Cleaning up S3 bucket ${ACCOUNT_ID}.fi.geoquery"
aws s3 rm s3://${ACCOUNT_ID}.fi.geoquery --recursive
aws s3api delete-bucket --bucket ${ACCOUNT_ID}.fi.geoquery 

echo "Deleting IAM Role... "
aws iam detach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam detach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTLogging
aws iam detach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration
aws iam delete-role --role-name blog-fi-geoquery-S3-access-role

#########
echo "Deleting local temporary file... "
rm -r provisioning
rm registration-task.json results.json role.json task-status.json root-CA.crt
rm -rf aws-iot-device-management-workshop

echo "Cleanup Done... "