#!/usr/bin/perl

use cPanelLicensing;

my $ip = '__IPTOADD__';

my $licenseManager = new cPanelLicensing(
    user => '__YOU@HOST.COM__',
    pass => '__YOURPASS__'
);

my (%LICENSES) = $licenseManager->fetchLicenses();

my (%GROUPS)   = $licenseManager->fetchGroups();
my (%PACKAGES) = $licenseManager->fetchPackages();

my $groupid   = $licenseManager->findKey( '__GROUPNAME__',   \%GROUPS );
my $packageid = $licenseManager->findKey( '__PACKAGENAME__', \%PACKAGES );

my $liscid = $licenseManager->activateLicense(
    'ip'        => $ip,
    'groupid'   => $groupid,
    'packageid' => $packageid,
    'force'     => 1,
    'reactivateok' =>
      0 #If 0 the license will not be activated if you would be billed a reactivation fee
       #If 1 the license will be activated if a fee is required (at the time of this writing, licenses reactivated within 72 hours of billing)
);

print "Added license with id: $liscid\n";

