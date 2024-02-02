# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


# when done, delete thing resources
input="results.json"
POLICY_NAME="blog_fi_geoquery_policy"
while read -r line
do
  #echo '--------'
  
  THING_NAME=$(jq -r '.response.ResourceArns.thing | split("/")[1]' <<< "$line")
  CERT_ARN=$(jq -r '.response.ResourceArns.certificate' <<< "$line")
  CERT_ID=$(jq -r '.response.ResourceArns.certificate | split("/")[1]' <<< "$line")
  #POLICY_NAME=$(jq -r '.response.ResourceArns.policy | split("/")[1]' <<< "$line")
  

  echo cleaning up $THING_NAME
  #echo $CERT_ARN
  #echo $CERT_ID
  #echo $POLICY_NAME
  
  echo "detaching policy.. "
  aws iot detach-policy --policy-name ${POLICY_NAME} --target ${CERT_ARN} --region us-east-1

  echo "detaching thing principal.. "
  aws iot detach-thing-principal --thing-name ${THING_NAME} --principal ${CERT_ARN} --region us-east-1

  echo "deleting certificate .. "
  aws iot update-certificate --certificate-id ${CERT_ID} --new-status INACTIVE --region us-east-1
  aws iot delete-certificate --certificate-id ${CERT_ID} --region us-east-1

  echo "removing thing from thing group.. "
  aws iot remove-thing-from-thing-group --thing-group-name blog-fi-geoquery-ebikes --thing-name ${THING_NAME} --region us-east-1
  
  echo "deleting thing.. "
  aws iot delete-thing --thing-name ${THING_NAME} --region us-east-1

done < "$input"


echo "deleting policy.. "
aws iot delete-policy --policy-name $POLICY_NAME --region us-east-1
echo "deleting thing group.. "
aws iot delete-thing-group --thing-group-name blog-fi-geoquery-ebikes --region us-east-1

