import boto3
import certbot.main
import datetime
import os
import raven
import subprocess

def should_provision(domain):
  existing_cert = find_cloudfront_dists(domain)
  if existing_cert:
    now = datetime.datetime.now(datetime.timezone.utc)
    not_after = existing_cert.get('Expiration')
    return (not_after - now).days
  else:
    return False

def find_cloudfront_dists(domain):
  session = boto3.Session(profile_name='certbot') # remove before upload to lambda

  client = session.client('cloudfront') 
  # client = boto3.client('cloudfront') 
  paginator = client.get_paginator('list_distributions')
  iterator = paginator.paginate(PaginationConfig={'MaxItems':1000})

  for page in iterator:
    for item in page['DistributionList'].get('Items'):
      items = frozenset(item.get('Aliases').get('Items'))
      if domain in items:
        cert_id = item.get('ViewerCertificate').get('IAMCertificateId')
        if cert_id is not None:
          return find_existing_cert(cert_id)
        else:
          return False

def find_existing_cert(cert_id):
  session = boto3.Session(profile_name='certbot') # remove before upload to lambda

  iam = session.client('iam')
  certs = iam.list_server_certificates()
  for cert in certs.get('ServerCertificateMetadataList'):
    print(cert.values())
    if cert_id in cert.values():
      return cert

def handler(event, context):
  # domains = os.environ['LETSENCRYPT_DOMAINS']
  domains = "aaronvb.com"
  domains = frozenset(domains.split(','))
  for domain in domains:
    if should_provision(domain):
      print('provision domain: %s' % domain)
    else:
      print('do not provision domain: %s' % domain)