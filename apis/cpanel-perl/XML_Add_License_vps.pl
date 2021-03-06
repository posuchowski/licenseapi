#!/usr/bin/perl

use cPanelLicensing;


my $ip = $ARGV[0];

my $licenseManager = new cPanelLicensing(user => 'company',
					pass => 'EB9uEROmOc0ZM4tH');

my (%GROUPS) = $licenseManager->fetchGroups();
my (%PACKAGES) = $licenseManager->fetchPackages();

my $groupid = $licenseManager->findKey('Company\*',\%GROUPS);
my $packageid = $licenseManager->findKey('COMPANY-INTERNAL-VZZO',\%PACKAGES);


my $liscid = $licenseManager->activateLicense(ip => $ip,
				groupid => $groupid,
				packageid => $packageid,
				force => 1,
				'reactivateok' => 1
				);

print "Added license with id: ${liscid}\n";

