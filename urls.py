from django.conf.urls import patterns, include, url

from handler import MethodHandler

json_handler = MethodHandler()

urlpatterns = patterns('',
    url( r'^json', json_handler.incoming, name='incoming_request' ),
)
