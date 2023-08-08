from django.contrib import admin
from django.urls import path
from . import views
from . import webviews, preview, cron
from . import share

from django.conf.urls import handler404, handler500

urlpatterns = [
    path('',webviews.index, name="index"),
    path('123', cron.logout_all_users, name="123"),
    
    # ##### Authentication #####
    path('login/', webviews.login, name="login"),
    path('logout/', webviews.logout, name="logout"),
    path('logout_11/', webviews.logout_11, name="logout_11"),
    path('password/forgot/', webviews.forgot, name="forgot"),
    path('clear-session', webviews.clear_session, name="clear-session"),
    path('view-profile', webviews.view_profile, name="view-profile"),
    path('add-user', webviews.add_user, name="add-user"),
    path('get-user', webviews.get_user, name="get-user"),
    path('view-dis-user', webviews.view_dis_user, name="view-dis-user"),
    path('update-user', webviews.update_user, name="update-user"),
    path('delete-user', webviews.delete_user, name="delete-user"),

    # ##### Settings #####
    path('settings', webviews.settings, name="settings"),
    path('update-email-configuration', webviews.update_email_configuration, name="update-email-configuration"),
    path('set-maintenance', webviews.set_maintenance, name="set-maintenance"),
    path('logout-all-server-users', webviews.logout_all_server_users, name="logout-all-server-users"),
    path('clear-storage', webviews.clear_storage, name="clear-storage"),

    ##### User Approval Section #####
    path('approve-user', webviews.approve_user, name="approve-user"),
    path('decline-user', webviews.decline_user, name="decline-user"),

    ##### Ajax Request #####
    path('share-multiple-doc', share.share_multiple_doc, name="share-multiple-doc"),
    path('share-multiple-doc-share', share.share_multiple_doc_share, name="share-multiple-doc-share"),
    path('share-multiple-dataentry-doc-share', share.share_multiple_dataentry_doc_share, name="share-multiple-dataentry-doc-share"),


    ##### Shareing Sectin #####
    path('share-doc', share.share_doc, name="share-doc"),
    path('share-doc-share', share.share_doc_share, name="share-doc-share"),
    path('preview-doc', preview.preview_doc, name="preview-doc"),
    path('change-download-status',share.change_download_status, name="change-download-status"),
    path('change-download-status-new',share.change_download_status_new, name="change-download-status-new"),

    ##### Sharing New Doc
    path('share-new-doc', share.share_new_doc, name="share-new-doc"),
    path('share-new-multiple-doc', share.share_new_multiple_doc, name="share-new-multiple-doc"),
    path('share-new-doc-share', share.share_new_doc_share, name="share-new-doc-share"),
    path('preview-new-doc', preview.preview_new_doc, name="preview-new-doc"),
    path('share-doc-to-user', share.share_new_doc, name="share-doc-to-user"),

    ##### DataEntry Doc
    path('get-dataentry-doc', webviews.get_dataentry_doc, name="get-dataentry-doc"),
    path('share-dataentry-doc-preview', webviews.share_dataentry_doc_preview, name="share-dataentry-doc-preview"),

    path('mainfun', webviews.mainfun, name="mainfun"),

    ##### State Section #####
    path('get-states', webviews.get_states, name="get-states"),
    path('add-state', webviews.add_state, name="add-state"),
    path('update-state', webviews.update_state, name="update-state"),
    path('delete-state', webviews.delete_state, name="delete-state"),

    ##### Limit Section #####
    path('get-limit', webviews.get_limit, name="get-limit"),
    # path('add-limit', webviews.add_limit, name="add-limit"),
    path('update-limit', webviews.update_limit, name="update-limit"),
    path('view-download-docs', webviews.view_download_docs, name="view-download-docs"),

    #Error redirecting page
    path('error/', views.error, name="error"),

]

handler404 = 'account.views.handler404'
handler500 = 'account.views.handler500'
handler403 = 'account.views.handler403'
