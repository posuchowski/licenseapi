#!/usr/bin/perl

use cPanelLicensing;

my $ip = '208.86.157.254';

my $licenseManager = new cPanelLicensing(user => 'company',
                                        pass => 'Ivghx4rPYIzeied5');



my $liscid_ref = $licenseManager->fetchLicenseRaw(ip => $ip);

print %$liscid_ref;

if ($liscid_ref) {
        my $liscid = $liscid_ref->{'licenseid'};
	my $status = $liscid_ref->{'status'};
	my $company = $liscid_ref->{'company'};

	if($liscid != "0")
		{
		print $status;		
		}
	else
		{
		print "0\n";
		}
}
