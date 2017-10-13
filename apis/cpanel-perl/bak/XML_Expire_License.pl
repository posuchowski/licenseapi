#!/usr/bin/perl

use cPanelLicensing;


my $ip = $ARGV[0];

my $licenseManager = new cPanelLicensing(user => 'wiredtree',
					pass => 'L68GuPOCfsuNr3td');


my $liscid = $licenseManager->fetchLicenseId(ip => $ip);
if ($liscid > 0) {
	my $result = $licenseManager->expireLicense(liscid => $liscid,
					reason => 'Automatic Removal');

	print "$result\n";
} else {
	print "There is no active license for ip address: ${ip}\n";
}
