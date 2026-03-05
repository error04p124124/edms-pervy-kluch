from django import template
from documents.permissions import (
    can_edit_document,
    can_delete_document,
    can_approve_document,
    can_manage_templates,
    can_view_all_documents,
    can_create_document,
)

register = template.Library()


@register.simple_tag
def user_can_edit_document(user, document):
    """Check if user can edit the document"""
    return can_edit_document(user, document)


@register.simple_tag
def user_can_delete_document(user, document):
    """Check if user can delete the document"""
    return can_delete_document(user, document)


@register.simple_tag
def user_can_approve_document(user, document):
    """Check if user can approve the document"""
    return can_approve_document(user, document)


@register.simple_tag
def user_can_manage_templates(user):
    """Check if user can manage templates"""
    return can_manage_templates(user)


@register.simple_tag
def user_can_view_all_documents(user):
    """Check if user can view all documents"""
    return can_view_all_documents(user)


@register.simple_tag
def user_can_create_document(user):
    """Check if user can create documents"""
    return can_create_document(user)
