#!/usr/bin/perl

package cPanelLicensing;

our $VERSION = 3.1;

use strict;
use Socket         ();
use Data::Dumper   ();
use Carp           ();
use LWP::UserAgent ();
use Net::SSLeay    ();

sub new {
    my ( $self, %OPTS ) = @_;

    $self = {};

    bless($self);

    $self->{'ua'} = LWP::UserAgent->new();
    $self->{'ua'}->agent( 'cPanel Licensing Agent (perl) ' . $VERSION );

    my @PARSERS = (
        [ 'XML::Simple', 'xml' ],
        [ 'JSON::Syck',  'json' ],
        [ 'YAML::Syck',  'yaml' ],
        [ 'YAML',        'yaml' ],
        [ 'JSON',        'json' ],
        [ 'JSON::XS',    'json' ],

    );

    foreach my $parser (@PARSERS) {
        my $parser_module = $parser->[0];
        my $parser_key    = $parser->[1];
        eval " require $parser_module; ";
        if ( !$@ ) {
            $self->{'parser_key'}    = $parser_key;
            $self->{'parser_module'} = $parser_module;
            last;
        }
    }
    if ($@) {
        Carp::confess(
            "Unable to find a module capable of parsing the api response.");
    }

    use XML::Simple ();

    if ( !exists( $OPTS{user} ) || $OPTS{'user'} eq '' ) {
        Carp::confess('Manage User Not Set');
    }
    if ( !exists( $OPTS{pass} ) || $OPTS{'pass'} eq '' ) {
        Carp::confess('Manage Password Not Set');
    }

    eval
"sub LWP::UserAgent::get_basic_credentials { return('$OPTS{'user'}','$OPTS{'pass'}'); }";

    return ($self);
}

sub reactivateLicense {
    my ( $self, %OPTS ) = @_;

    my $liscid = $OPTS{'liscid'};
    my $licref =
      $self->_HashReq(
            'https://manage2.cpanel.net/XMLlicenseReActivate.cgi?liscid=' 
          . $liscid
          . '&reactivateok=' . ($OPTS{'reactivateok'} ? 1 : 0) 
          . '&output='
          . $self->{'parser_key'} );

    return ( $$licref{'licenseid'} );
}

sub expireLicense {
    my ( $self, %OPTS ) = @_;

    my (%FORM);

    $FORM{'liscid'} = $OPTS{'liscid'};
    $FORM{'reason'} = $OPTS{'reason'};
    $FORM{'expcode'} = $OPTS{'expcode'};
    $FORM{'output'} = $self->{'parser_key'};

    my $response =
      $self->{'ua'}
      ->post( 'https://manage2.cpanel.net/XMLlicenseExpire.cgi', \%FORM );

    my ($resultref);
    if ( $response->is_success ) {
        $resultref = $self->parseResponse( $response->content );
    }
    else {
        Carp::confess( $response->status_line );
    }

    if ( int( $$resultref{'status'} ) != 1 ) {
        Carp::confess( "Failed to expire license: "
              . $$resultref{'reason'} . "\n"
              . Data::Dumper::Dumper($resultref) );
    }

    return ( $$resultref{'result'} );
}

sub extend_onetime_updates {
    my ( $self, %OPTS ) = @_;

    my %FORM;
    $FORM{'ip'}     = Socket::inet_ntoa( Socket::inet_aton( $OPTS{'ip'} ) );

    my $response =
      $self->{'ua'}
      ->post( 'https://manage2.cpanel.net/XMLonetimeext.cgi', \%FORM );

    my ($resultref);
    if ( $response->is_success ) {
        $resultref = $self->parseResponse( $response->content );
    }
    else {
        Carp::confess( $response->status_line );
    }

    return ( $resultref->{'status'}, $resultref->{'reason'} );
}


sub changeip {
    my ( $self, %OPTS ) = @_;

    my %FORM;
    $FORM{'output'} = $self->{'parser_key'};
    $FORM{'oldip'}     = Socket::inet_ntoa( Socket::inet_aton( $OPTS{'oldip'} ) );
    $FORM{'newip'}     = Socket::inet_ntoa( Socket::inet_aton( $OPTS{'newip'} ) );

    my $response =
      $self->{'ua'}
      ->post( 'https://manage2.cpanel.net/XMLtransfer.cgi', \%FORM );

    my ($resultref);
    if ( $response->is_success ) {
        $resultref = $self->parseResponse( $response->content );
    }
    else {
        Carp::confess( $response->status_line );
    }

    return ( $resultref->{'status'}, $resultref->{'reason'} );
}


sub requestTransfer {
    my ( $self, %OPTS ) = @_;

    my %FORM;
    if ( int( $OPTS{'groupid'} ) == 0 ) {
        Carp::confess('Group Id is not valid');
    }
    $FORM{'groupid'} = int( $OPTS{'groupid'} );
    if ( int( $OPTS{'packageid'} ) == 0 ) {
        Carp::confess('Package Id is not valid');
    }
    $FORM{'packageid'} = int( $OPTS{'packageid'} );
    if ( $OPTS{'ip'} eq '' ) {
        Carp::confess('Ip Address is not valid');
    }
    $FORM{'output'} = $self->{'parser_key'};
    $FORM{'ip'}     = Socket::inet_ntoa( Socket::inet_aton( $OPTS{'ip'} ) );

    my $response =
      $self->{'ua'}
      ->post( 'https://manage2.cpanel.net/XMLtransferRequest.cgi', \%FORM );

    my ($resultref);
    if ( $response->is_success ) {
        $resultref = $self->parseResponse( $response->content );
    }
    else {
        Carp::confess( $response->status_line );
    }

    return ( $resultref->{'status'}, $resultref->{'reason'} );
}

sub activateLicense {
    my ( $self, %OPTS ) = @_;

    my (%FORM);
    $FORM{'output'} = $self->{'parser_key'};

    $FORM{'legal'} = 1;    #customer is responsible for verifing this
    if ( int( $OPTS{'groupid'} ) == 0 ) {
        Carp::confess('Group Id is not valid');
    }
    $FORM{'groupid'} = int( $OPTS{'groupid'} );
    if ( int( $OPTS{'packageid'} ) == 0 ) {
        Carp::confess('Package Id is not valid');
    }
    $FORM{'packageid'} = int( $OPTS{'packageid'} );
    $FORM{'force'}     = int( $OPTS{'force'} );
    $FORM{'reactivateok'} = int ($OPTS{'reactivateok'});          
                 
    if ( $OPTS{'ip'} eq '' ) {
        Carp::confess('Ip Address is not valid');
    }
    $FORM{'ip'} = Socket::inet_ntoa( Socket::inet_aton( $OPTS{'ip'} ) );

    my $response =
      $self->{'ua'}
      ->post( 'https://manage2.cpanel.net/XMLlicenseAdd.cgi', \%FORM );

    my ($resultref);
    if ( $response->is_success ) {
        $resultref = $self->parseResponse( $response->content );
    }
    else {
        Carp::confess( $response->status_line );
    }

    if ( int( $$resultref{'status'} ) != 1 ) {
        Carp::confess( "Failed to add license: "
              . $$resultref{'reason'} . "\n"
              . Data::Dumper::Dumper($resultref) );
    }

    return ( $$resultref{'licenseid'} );
}

sub findKey {
    my ( $self, $searchkey, $href ) = @_;
		my $regex;
		
		if ( $searchkey ) {
			eval {
				local $SIG{'__DIE__'} = sub { return };
				$regex = qr/^$searchkey$/i;
			};
		}

		if ( !$regex ) {
			Carp::confess("Regular Expression generation failure");
			return;
		} else {
			foreach my $key ( keys %{ $href } ) {
				if ($href->{$key} =~ $regex) {
					return $key
				}
			}
		}
    Carp::confess( "Key ${searchkey} not found in hash:\n" . Data::Dumper::Dumper($href) );
}

sub fetchGroups {
    my $self = shift;
    my $groupsref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLgroupInfo.cgi'
          . '?output='
          . $self->{'parser_key'} );

    _stripType( $$groupsref{'groups'} );

    return ( %{ $$groupsref{'groups'} } );
}

sub fetchLicenseRiskData {
    my ( $self, %OPTS ) = @_;

    my $ip = $OPTS{'ip'};
    my $licref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLsecverify.cgi?ip=' 
          . $ip
          . '&output='
          . $self->{'parser_key'} );

    return ($licref);
}

sub fetchLicenseRaw {
    my ( $self, %OPTS ) = @_;

    my $ip = $OPTS{'ip'};
    my $licref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLRawlookup.cgi?ip=' 
          . $ip
          . '&output='
          . $self->{'parser_key'} );

    return ($licref);
}

sub fetchLicenseId {
    my ( $self, %OPTS ) = @_;

    my $ip = $OPTS{'ip'};
    my $licref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLlookup.cgi?ip=' 
          . $ip
          . '&output='
          . $self->{'parser_key'} );

    return ( $$licref{'licenseid'} );
}

sub fetchPackages {
    my $self = shift;
    my $packagesref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLpackageInfo.cgi'
          . '?output='
          . $self->{'parser_key'} );

    _stripType( $$packagesref{'packages'} );

    return ( %{ $$packagesref{'packages'} } );
}

sub fetchLicenses {
    my $self = shift;
    my $licensesref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLlicenseInfo.cgi'
          . '?output='
          . $self->{'parser_key'} );

    _stripType( $$licensesref{'licenses'} );

    return ( %{ $$licensesref{'licenses'} } );
}

sub fetchExpiredLicenses {
    my $self = shift;
    my $licensesref =
      $self->_HashReq( 'https://manage2.cpanel.net/XMLlicenseInfo.cgi?expired=1'
          . '&output='
          . $self->{'parser_key'} );

    _stripType( $$licensesref{'licenses'} );

    return ( %{ $$licensesref{'licenses'} } );
}

sub _stripType {
    my ($href) = @_;

    #strips of the first letter of the ID (ie P1213 becomes 1213)
    foreach my $key ( keys %{$href} ) {

        $$href{ substr( $key, 1 ) } = $$href{$key};
        delete $$href{$key};
    }

}

sub _HashReq {
    my $self = shift;
    my $url  = shift;

    my $response = $self->{'ua'}->get($url);

    my ($sref);
    if ( $response->is_success ) {
        $sref = $self->parseResponse( $response->content );

        if ( int( $$sref{'status'} ) != 1 ) {
            Carp::confess( "Failed to process request: "
                  . $$sref{'reason'} . "\n"
                  . Data::Dumper::Dumper($sref) );
        }

    }
    else {
        Carp::confess( $response->status_line );
    }

    return ($sref);
}

sub parseResponse {
    my ( $self, $content ) = @_;
    my $ref;

    if ( $self->{'parser_module'} eq 'JSON::Syck' ) {
        eval { $ref = JSON::Syck::Load($content); };
    }
    elsif ( $self->{'parser_module'} eq 'JSON' ) {
        eval { $ref = JSON::from_json($content); };
    }
    elsif ( $self->{'parser_module'} eq 'JSON::XS' ) {
        eval { $ref = JSON::XS::decode_json($content); };
    }
    elsif ( $self->{'parser_module'} eq 'YAML' ) {
        eval { $ref = YAML::Load($content); };
    }
    elsif ( $self->{'parser_module'} eq 'YAML::Syck' ) {
        eval { $ref = YAML::Syck::Load($content); };
    }
    elsif ( $self->{'parser_module'} eq 'XML::Simple' ) {
        eval { $ref = XML::Simple::XMLin($content); };
    }

    if ( !$ref ) {
        Carp::confess(
"Unable to parse $self->{'parser_key'}: error:$! eval_error:$@ content:$content."
        );
    }
    return $ref;
}
1;
