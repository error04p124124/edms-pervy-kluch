from django.contrib import admin
from .models import (DocumentTemplate, Document, DocumentHistory, Notification, WorkflowStep, 
                      ChatMessage, QuickTemplate, WorkflowApproval, TeamStats,
                      DocumentVersion, DocumentComment, Task, DocumentAttachment, AuditLog, ElectronicSignature)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'


class DocumentHistoryInline(admin.TabularInline):
    model = DocumentHistory
    extra = 0
    readonly_fields = ('user', 'action', 'comment', 'created_at')
    can_delete = False


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('version_number', 'created_by', 'created_at')
    can_delete = False
    fields = ('version_number', 'title', 'changes_description', 'created_by', 'created_at')


class DocumentCommentInline(admin.StackedInline):
    model = DocumentComment
    extra = 0
    readonly_fields = ('author', 'created_at', 'updated_at')
    fields = ('author', 'text', 'created_at', 'updated_at', 'is_edited')


class DocumentAttachmentInline(admin.TabularInline):
    model = DocumentAttachment
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at', 'file_size')


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    readonly_fields = ('completed_at',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('registry_number', 'title', 'status', 'created_by', 'assigned_to', 'created_at', 'deadline', 'is_overdue')
    list_filter = ('status', 'template__type', 'created_at', 'deadline')
    search_fields = ('registry_number', 'title', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('registry_number', 'created_at', 'updated_at')
    inlines = [WorkflowStepInline, DocumentHistoryInline, DocumentVersionInline, 
               DocumentCommentInline, DocumentAttachmentInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('registry_number', 'title', 'template', 'status', 'version')
        }),
        ('Пользователи', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Содержание', {
            'fields': ('content', 'file', 'generated_file')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'deadline')
        }),
        ('Маршрутизация', {
            'fields': ('workflow_route', 'current_step', 'approval_type'),
            'classes': ('collapse',)
        }),
        ('Версионность', {
            'fields': ('parent_version',),
            'classes': ('collapse',)
        }),
        ('Электронная подпись', {
            'fields': ('is_signed', 'signed_at', 'signed_by'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочен'


@admin.register(DocumentHistory)
class DocumentHistoryAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'created_at')
    list_filter = ('created_at', 'action')
    search_fields = ('document__title', 'action', 'comment')
    date_hierarchy = 'created_at'
    readonly_fields = ('document', 'user', 'action', 'comment', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'document', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Отметить как прочитанное'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = 'Отметить как непрочитанное'


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('document', 'step_number', 'user', 'status', 'completed_at')
    list_filter = ('status', 'completed_at')
    search_fields = ('document__title', 'user__username')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'message_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('sender', 'recipient', 'created_at')
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Сообщение'




@admin.register(QuickTemplate)
class QuickTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_type', 'created_by', 'is_active', 'usage_count', 'created_at')
    list_filter = ('document_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('usage_count', 'created_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'document_type', 'description', 'is_active')
        }),
        ('Шаблон', {
            'fields': ('content_template',)
        }),
        ('Метаданные', {
            'fields': ('created_by', 'usage_count', 'created_at')
        }),
    )


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    list_display = ('workflow_step', 'approver', 'decision', 'decision_date', 'created_at')
    list_filter = ('decision', 'decision_date', 'created_at')
    search_fields = ('workflow_step__document__title', 'approver__username', 'comments')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('workflow_step', 'approver', 'decision')
        }),
        ('Решение', {
            'fields': ('comments', 'decision_date', 'delegated_to')
        }),
        ('Метаданные', {
            'fields': ('created_at',)
        }),
    )


@admin.register(TeamStats)
class TeamStatsAdmin(admin.ModelAdmin):
    list_display = ('manager', 'date', 'documents_created', 'documents_approved', 'documents_rejected', 'team_members_count')
    list_filter = ('date',)
    search_fields = ('manager__username', 'manager__first_name', 'manager__last_name')
    date_hierarchy = 'date'
    readonly_fields = ('date',)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title', 'title', 'changes_description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'author', 'text_preview', 'created_at', 'is_edited')
    list_filter = ('created_at', 'is_edited')
    search_fields = ('document__title', 'author__username', 'text')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('mentions',)
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'status', 'priority', 'deadline', 'is_overdue', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'deadline')
    search_fields = ('title', 'description', 'assigned_to__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'document')
        }),
        ('Назначение', {
            'fields': ('assigned_to', 'created_by', 'status', 'priority')
        }),
        ('Сроки', {
            'fields': ('deadline', 'completed_at', 'created_at', 'updated_at')
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'


@admin.register(DocumentAttachment)
class DocumentAttachmentAdmin(admin.ModelAdmin):
    list_display = ('document', 'original_filename', 'file_size_mb', 'file_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('document__title', 'original_filename', 'description')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at', 'file_size')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'object_type', 'object_repr', 'ip_address', 'created_at')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('user__username', 'object_repr', 'ip_address', 'details')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'object_type', 'object_id', 'object_repr', 
                       'ip_address', 'user_agent', 'details', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ElectronicSignature)
class ElectronicSignatureAdmin(admin.ModelAdmin):
    list_display = ('document', 'signer', 'signed_at', 'is_valid', 'ip_address')
    list_filter = ('is_valid', 'signed_at')
    search_fields = ('document__title', 'signer__username', 'certificate_info')
    date_hierarchy = 'signed_at'
    readonly_fields = ('signed_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('document', 'signer', 'is_valid')
        }),
        ('Подпись', {
            'fields': ('signature_data', 'certificate_info')
        }),
        ('Метаданные', {
            'fields': ('signed_at', 'ip_address')
        }),
    )
