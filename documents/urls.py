from django.urls import path
from . import views
from . import views_extended

app_name = 'documents'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Documents
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/create/', views.DocumentCreateView.as_view(), name='document_create'),
    path('documents/create-from-template/', views.create_from_template, name='create_from_template'),
    path('documents/template-placeholders/<int:pk>/', views.template_placeholders_json, name='template_placeholders_json'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('documents/<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_edit'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('documents/<int:pk>/register/', views.register_document, name='register_document'),
    path('documents/<int:pk>/archive/', views.archive_document, name='archive_document'),
    path('documents/<int:pk>/workflow/', views.setup_workflow, name='setup_workflow'),
    path('documents/<int:pk>/approve/', views.approve_document, name='approve_document'),
    path('workflow-step/<int:step_id>/approve/', views.approve_workflow_step, name='approve_workflow_step'),
    path('documents/<int:pk>/download/', views.download_generated_file, name='download_generated'),
    path('documents/bulk-archive/', views.bulk_archive, name='bulk_archive'),
    
    # Комментарии
    path('documents/<int:document_id>/comments/add/', views_extended.add_comment, name='add_comment'),
    path('documents/<int:document_id>/comments/', views_extended.get_comments, name='get_comments'),
    path('comments/<int:comment_id>/edit/', views_extended.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', views_extended.delete_comment, name='delete_comment'),
    
    # Задачи
    path('tasks/', views_extended.task_list, name='task_list'),
    path('tasks/create/', views_extended.create_task, name='create_task'),
    path('tasks/<int:task_id>/status/', views_extended.update_task_status, name='update_task_status'),
    
    # Версии документов
    path('documents/<int:document_id>/versions/', views_extended.document_versions, name='document_versions'),
    path('documents/<int:document_id>/versions/create/', views_extended.create_version, name='create_version'),
    path('versions/<int:version_id>/restore/', views_extended.restore_version, name='restore_version'),
    
    # Электронная подпись
    path('documents/<int:document_id>/sign/', views_extended.sign_document_view, name='sign_document'),
    path('documents/<int:document_id>/signatures/', views_extended.document_signatures, name='document_signatures'),
    
    # Архив
    path('documents/<int:document_id>/archive/', views_extended.archive_document_view, name='archive_document_new'),
    path('documents/<int:document_id>/restore/', views_extended.restore_document_view, name='restore_document'),
    path('archive/', views_extended.archive_list, name='archive_list'),
    
    # Экспорт и печать
    path('documents/<int:document_id>/export/pdf/', views_extended.export_document_pdf, name='export_pdf'),
    path('documents/<int:document_id>/print/', views_extended.print_document, name='print_document'),
    
    # Вложения
    path('documents/<int:document_id>/attachments/upload/', views_extended.upload_attachment, name='upload_attachment'),
    path('attachments/<int:attachment_id>/delete/', views_extended.delete_attachment, name='delete_attachment'),
    
    # Уведомления (расширенные)
    path('notifications/', views_extended.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views_extended.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views_extended.mark_all_notifications_read, name='mark_all_read_new'),
    path('api/notifications/count/', views_extended.unread_notifications_count, name='notifications_count'),
    
    # API
    path('api/templates/<int:template_id>/placeholders/', views_extended.get_template_placeholders, name='template_placeholders_api'),
    
    # Templates
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.TemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.TemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<int:pk>/download/', views.download_template_file, name='download_template'),
    path('templates/<int:template_id>/generate/', views.generate_document_auto, name='generate_document_auto'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/excel/', views.report_export_excel, name='report_export_excel'),
    path('reports/export/pdf/',   views.report_export_pdf,   name='report_export_pdf'),
    path('reports/export/docx/',  views.report_export_docx,  name='report_export_docx'),
    
    # Old Notifications (сохранены для совместимости)
    path('notifications-old/', views.notifications_list, name='notifications'),
    path('notifications-old/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read_old'),
    path('notifications-old/read-all/', views.mark_all_notifications_read, name='mark_all_read_old'),
    
    # Chat
    path('chat/', views.chat_page, name='chat'),
    path('chat/<int:active_user_id>/', views.chat_page, name='chat_with_user'),

    # Chat API
    path('api/chat/users/', views.chat_users_list, name='chat_users'),
    path('api/chat/messages/<int:user_id>/', views.chat_messages, name='chat_messages'),
    path('api/chat/send/', views.chat_send_message, name='chat_send'),
    path('api/chat/unread/', views.chat_unread_count, name='chat_unread'),
    
    # Clerk - Quick Templates
    path('quick-templates/', views.quick_templates, name='quick_templates'),
    path('quick-templates/<int:template_id>/create/', views.create_from_quick_template, name='create_from_quick_template'),
    
    # Manager - Approvals & Statistics
    path('approvals/', views.manager_approvals, name='manager_approvals'),
    path('approvals/<int:approval_id>/process/', views.process_approval, name='process_approval'),
]

