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
    (r'^$', login_teacher),
    (r'^micromessage/$', handleRequest),
    (r'^solved/', solved),
    (r'^unsolved/', unsolved),
    (r'^test/$', test),
    (r'^single_question/', single_question),
    (r'^login_teacher/', login_teacher),
    (r'^questions_teacher/$', questions_teacher),
    (r'^answerQuestion/$',answer),
    (r'^register_teacher/$',register_teacher),
    (r'^checkQuestion/$',checkQuestion),
    (r'^questions_unEvaluate/$', questions_unEvaluate),
    (r'^replayQuestion/$',replayQuestion),
    (r'^questions_solved/$',questions_solved),
    (r'^profile_teacher/$', profile_teacher),
    (r'^exchange_teacher/$', exchange_teacher),
    (r'^logout_teacher/$', logout_teacher),
    (r'^user_info/', user_info),
    (r'', not_found),
)
