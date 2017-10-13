#!/usr/bin/perl

use cPanelLicensing;

my $ip = '__IPTOLOOKUP__';

my $licenseManager = new cPanelLicensing(user => '__YOU@HOST.COM__',
                                        pass => '__YOURPASS__');

my $liscid = $licenseManager->fetchLicenseId(ip => $ip);
if ($liscid > 0) {
	print "The license id for ip address: ${ip} is: ${liscid}\n";
} else {
	print "There is no active license for ip address: ${ip}\n";
}
