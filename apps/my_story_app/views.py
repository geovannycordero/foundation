from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry
from .serializers import MyStoryTextComponentEntrySerializer, MyStoryTextComponentSerializer, MyStoryTabSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def track_tab_click(request):
    resp = {}
    resp['success'] = False
    if request.POST.get("tab_id", None):
        tab_info = MyStoryTab.objects.get(id=request.POST.get("tab_id", None))
        if permissions_accessed(request.user, tab_info.patient.id):
            actor = request.user
            patient = tab_info.patient

            summary = "<b>%s</b> accessed %s" % (actor.username, tab_info.name)
            op_add_event(actor, patient, summary)
            resp['success'] = True

    return ajax_response(resp)

@login_required
def get_my_story(request, patient_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        tabs = MyStoryTab.objects.filter(patient_id=int(patient_id))
        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(tabs, many=True).data
    return ajax_response(resp)

@login_required
def get_tab_info(request, tab_id):
    resp = {}
    resp['success'] = False
    tab_info = MyStoryTab.objects.get(id=tab_id)
    if permissions_accessed(request.user, tab_info.patient.id):
        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(tab_info).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def add_tab(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.create(patient_id=int(patient_id),
                                       author=request.user,
                                       name=request.POST.get("name", None))

        private = True if request.POST.get('private', False) else False
        tab.private = private
        tab.save()

        resp['tab'] = MyStoryTabSerializer(tab).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def add_text(request, patient_id, tab_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        patient_user = User.objects.get(id=patient_id)

        text = MyStoryTextComponent()
        text.name = request.POST.get("name", None)
        text.text = request.POST.get("text", None)
        text.concept_id = request.POST.get("concept_id", None)

        private = True if request.POST.get('private', False) else False
        text.private = private

        text.patient = patient_user
        text.author = request.user
        text.last_updated_user = request.user
        text.tab = tab
        text.save()

        resp['component'] = MyStoryTextComponentSerializer(text).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def delete_tab(request, patient_id, tab_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        if request.user.id == tab.author.id:
            MyStoryTextComponentEntry.objects.filter(component__tab=tab).delete()
            MyStoryTextComponent.objects.filter(tab=tab).delete()
            tab.delete()
        
            resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def save_tab(request, patient_id, tab_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        tab.name = request.POST.get("name", None)
        tab.save()
        
        resp['tab'] = MyStoryTabSerializer(tab).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def delete_text_component(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = MyStoryTextComponent.objects.get(id=int(component_id))
        if request.user.id == component.author.id:
            MyStoryTextComponentEntry.objects.filter(component=component).delete()
            component.delete()
        
            resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["save_text_component"])
def save_text_component(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = MyStoryTextComponent.objects.get(id=int(component_id))
        if request.POST.get("name", None):
            component.name = request.POST.get("name", None)
        if request.POST.get("text", None):
            entry = MyStoryTextComponentEntry(component=component, text=component.text, datetime=component.datetime, private=component.private, author=component.author)
            entry.save()

            component.text = request.POST.get("text", None)
            component.last_updated_user = request.user

            resp['entry'] = MyStoryTextComponentEntrySerializer(entry).data

        component.save()
        
        resp['component'] = MyStoryTextComponentSerializer(component).data
        resp['success'] = True

    return ajax_response(resp)