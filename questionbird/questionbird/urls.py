from django.conf.urls import patterns, include, url

from django.contrib import admin
from questionbird.views import *
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Question_Bird.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    #url(r'^admin/', include(admin.site.urls)),
    (r'^test/$', test),
    (r'', handleRequest),
)
