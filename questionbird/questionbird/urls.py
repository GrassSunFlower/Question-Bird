from django.conf.urls import patterns, include, url

from django.contrib import admin
from questionbird.views import *
import settings
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Question_Bird.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    #url(r'^admin/', include(admin.site.urls)),
    (r'^site_media/(?P<path>.*)$','django.views.static.serve', {'document_root':settings.STATIC_PATH}),
    (r'^$', index),
    (r'^micromessage/$', handleRequest),
    (r'^login/', login),
    (r'^register/', register),
    (r'^solved/', solved),
    (r'^unsolved/', unsolved),
    #(r'^loginform/', loginform),
    (r'^test/$', test),
    (r'^login_teacher/', login_teacher),
    (r'^questions_teacher/$', questions_teacher),
    (r'^answerQuestion/$',answer),
    (r'^register_teacher/$',register_teacher),
)
