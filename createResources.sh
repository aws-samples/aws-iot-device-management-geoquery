# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0



if [[ $# -ne 2 ]] ; then
    echo 'please input the 'thing name' and the 'number of things' to create.. '
    exit 1
fi

THING_NAME=$1
NO_OF_THINGS=$2

ACCOUNT_ID=`aws sts get-caller-identity --query "Account" --output text`
S3_BUCKET=${ACCOUNT_ID}.fi.geoquery

THING_TYPE="ev-charger"
THING_GROUP="blog-fi-geoquery-evchargers"

echo "Cloning repository.."
git clone https://github.com/aws-samples/aws-iot-device-management-workshop.git

echo "Creating S3 bucket ${S3_BUCKET} "
aws s3api create-bucket --bucket ${S3_BUCKET} --region us-east-1

echo "Create an IAM role allowing access to IoT core on the S3 bucket"
aws iam create-role --role-name blog-fi-geoquery-S3-access-role --assume-role-policy-document file://s3-access-role.json | tee role.json
aws iam attach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam attach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTLogging
aws iam attach-role-policy --role-name blog-fi-geoquery-S3-access-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration
ARN_IOT_PROVISIONING_ROLE=$(jq -r '.Role.Arn' < role.json)
echo "Role Created : " ${ARN_IOT_PROVISIONING_ROLE}
sleep 5

# create bulk provisioning file 
echo "creating bulk provisioning file..."
mkdir provisioning
cd provisioning
bash ../aws-iot-device-management-workshop/bin/mk-bulk.sh ${THING_NAME} ${NO_OF_THINGS}
DIR_NAME=`ls`
cd ..

echo "copy bulk.json to S3..."
aws s3 cp provisioning/${DIR_NAME}/bulk.json s3://${S3_BUCKET}/
# verify that the file was copied
aws s3 ls s3://${S3_BUCKET}/
mv provisioning/${DIR_NAME}/*.key provisioning


echo "Create Thing Type, Thing Group and Thing Policy..."
aws iot create-thing-type --thing-type-name ${THING_TYPE} --region us-east-1
aws iot create-thing-group --thing-group-name ${THING_GROUP} --region us-east-1
aws iot create-policy --policy-name blog_fi_geoquery_policy --region us-east-1 --policy-document file://blog_fi_geoquery_policy.json

echo "Start thing registration task... "
aws iot start-thing-registration-task \
  --template-body file://templateBody.json \
  --input-file-bucket ${S3_BUCKET} \
  --input-file-key bulk.json --role-arn ${ARN_IOT_PROVISIONING_ROLE} \
  --region us-east-1 | tee registration-task.json
 
TASK_ID=$(jq -r '.taskId' < registration-task.json)
echo "registration task id: " ${TASK_ID}

echo "Waiting for task to complete... "

while :
do
   sleep 5
   aws iot describe-thing-registration-task --task-id ${TASK_ID} --region us-east-1 | tee task-status.json
   status=$(jq -r '.status' < task-status.json)
   
   if [ ${status} != "Completed" ]
   then
       continue
   else
       failureCount=$(jq -r '.failureCount' < task-status.json)
       successCount=$(jq -r '.successCount' < task-status.json)
       break
   fi
done

if [ ${failureCount} -gt 0 ]
then 
    echo failureCount $failureCount
    #aws iot list-thing-registration-task-reports --task-id ${TASK_ID} --region us-east-1 --report-type ERRORS
    wget -O errors.json $(aws iot list-thing-registration-task-reports --task-id ${TASK_ID} --region us-east-1 --report-type ERRORS | jq -r '.resourceLinks[]')
    echo "see errors.json for details of failure... exiting"
    exit 1
    
fi

if [ ${successCount} -gt 0 ]
then 
    echo successCount $successCount
    wget -O results.json $(aws iot list-thing-registration-task-reports --task-id ${TASK_ID} --region us-east-1 --report-type RESULTS | jq -r '.resourceLinks[]')
    
fi

cd provisioning

echo "Extracting certificates from registration result..."
../aws-iot-device-management-workshop/bin/bulk-result.py ../results.json
ls -l
cd ..

#aws iot list-things ${THING_NAME}*
