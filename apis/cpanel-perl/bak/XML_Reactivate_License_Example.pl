#!/usr/bin/perl

use cPanelLicensing;

my $ip = '__IPTOREACTIVATE__';

my $licenseManager = new cPanelLicensing(user => '__YOU@HOST.COM__',
                                        pass => '__YOURPASS__');

my $liscid = $licenseManager->fetchLicenseId(ip => $ip);
if ($liscid > 0) {
	my $result = $licenseManager->reactivateLicense(liscid => $liscid);
	if ($result > 0) {
		print "$result has been reactivated\n";
	} else {
		print "Unable to reactivate license!\n";
	}
} else {
	print "There is no active license for ip address: ${ip}\n";
}
