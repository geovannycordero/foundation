#!/usr/bin/env python
from dateutil import parser

from document_app.serializers import DocumentSerialization
from encounters_app.serializers import EncounterSerializer

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

import operator

from django.db.models import Max, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from a1c_app.serializers import AOneCSerializer
from colons_app.serializers import ColonCancerScreeningSerializer
from common.views import *
from data_app.serializers import ObservationPinToProblemSerializer, ObservationSerializer
from emr.models import ColonCancerScreening
from emr.models import Encounter
from emr.models import Goal, ToDo, TextNote, PatientImage, Label
from emr.models import MedicationPinToProblem
from emr.models import ProblemNote, ProblemActivity, CommonProblem
from emr.models import ProblemRelationship
from emr.models import SharingPatient, PhysicianTeam, AOneC, ObservationPinToProblem
from emr.models import UserProfile, Problem, ProblemOrder, ProblemLabel, LabeledProblemList
from emr.operations import op_add_event, op_add_todo_event
from emr.serializers import TextNoteSerializer
from goals_app.serializers import GoalSerializer
from medication_app.serializers import MedicationPinToProblemSerializer
from problems_app.operations import add_problem_activity
from problems_app.services import ProblemService
from todo_app.operations import add_todo_activity
from todo_app.serializers import TodoSerializer
from users_app.serializers import UserProfileSerializer
from .serializers import ProblemNoteSerializer, ProblemActivitySerializer, CommonProblemSerializer, \
    PatientImageSerializer
from .serializers import ProblemSerializer, ProblemLabelSerializer, \
    LabeledProblemListSerializer, ProblemInfoSerializer


@login_required
def track_problem_click(request, problem_id):
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if actor_profile.role in ['physician', 'admin']:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        summary = "Clicked <u>problem</u>: <b>%s</b>" % problem.problem_name
        op_add_event(actor, patient, summary)

        activity = "Visited <u>problem</u>: <b>%s</b>" % problem.problem_name
        add_problem_activity(problem, actor_profile, activity)

    resp = {}
    return ajax_response(resp)


@login_required
def get_problem_info(request, problem_id):
    """
    Loading problem details
    :param request:
    :param problem_id:
    :return:
    """
    start_time = datetime.now()

    sharing_patients_list = []

    problem_info = Problem.objects.select_related("patient").prefetch_related("target", "source",
                                                                              "problem_aonecs", ).get(id=problem_id)

    # Add a1c widget to problems that have concept id 73211009, 46635009, 44054006
    if problem_info.concept_id in ['73211009', '46635009', '44054006']:
        AOneC.objects.create_if_not_exist(problem_info)

    # Add colon cancer widget to problems that have concept id 102499006
    if problem_info.concept_id in ['102499006']:
        ColonCancerScreening.objects.create_if_not_exist(problem_info)

    serialized_problem = ProblemInfoSerializer(problem_info).data

    sharing_patients = SharingPatient.objects.filter(
        shared=problem_info.patient).order_by('sharing__first_name', 'sharing__last_name')

    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    resp = {
        'success': True,
        'info': serialized_problem,
        'effecting_problems': serialized_problem["effecting_problems"],
        'effected_problems': serialized_problem["effected_problems"],
        'patient_problems': serialized_problem["patient_other_problems"],
        'a1c': serialized_problem["a1c"],
        'colon_cancer': serialized_problem["colon_cancer"],
        'sharing_patients': sharing_patients_list
    }
    end_time = datetime.now()
    print ("get_problem_info exec time: {0}".format(end_time - start_time))

    return ajax_response(resp)


@login_required
def get_a1c(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    resp = {'success': False}
    if hasattr(problem, 'problem_aonecs'):
        a1c = problem.problem_aonecs
        serialized_a1c = AOneCSerializer(a1c).data
        resp = {'success': True, 'a1c': serialized_a1c}
    return ajax_response(resp)


@login_required
def get_colon_cancers(request, problem_id):
    resp = {'success': False}

    colon_cancers = ColonCancerScreening.objects.filter(problem__id=problem_id)
    serialized_colon_cancers = ColonCancerScreeningSerializer(colon_cancers, many=True).data

    resp['success'] = True
    resp['colon_cancers'] = serialized_colon_cancers
    return ajax_response(resp)


@login_required
def get_problem_activity(request, problem_id, last_id):
    resp = {'success': False}

    problem = get_object_or_404(Problem, pk=problem_id)
    activities = ProblemActivity.objects.filter(problem=problem).filter(id__gt=last_id)
    activity_holder = ProblemActivitySerializer(activities, many=True).data

    resp['activities'] = activity_holder
    resp['success'] = True
    return ajax_response(resp)


# Problem
@permissions_required(["add_problem"])
@login_required
@api_view(["POST"])
def add_patient_problem(request, patient_id):
    resp = {'success': False}
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    term = request.POST.get('term')

    concept_id = request.POST.get('code', None)
    if Problem.objects.filter(problem_name=term, patient__id=patient_id).exists():
        return ajax_response({"msg": "Problem already added"})

    new_problem = Problem.objects.create_new_problem(patient_id, term, concept_id, actor_profile)
    physician = request.user

    summary = 'Added <u>problem</u> <b>%s</b>' % term
    op_add_event(physician, new_problem.patient, summary, new_problem)
    activity = "Added <u>problem</u>: <b>%s</b>" % term
    add_problem_activity(new_problem, actor_profile, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@permissions_required(["add_problem"])
@login_required
# @api_view(["POST"])
def add_patient_common_problem(request, patient_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    cproblem = request.POST.get('cproblem')
    problem_type = request.POST.get('type')

    problem = CommonProblem.objects.get(id=cproblem)

    if Problem.objects.filter(problem_name=problem.problem_name, concept_id=problem.concept_id,
                              patient__id=patient_id).exists():
        return ajax_response({"msg": "Problem already added"})

    new_problem = Problem.objects.create_new_problem(patient_id, problem.problem_name, problem.concept_id,
                                                     actor_profile)
    physician = request.user

    summary = 'Added <u>problem</u> <b>%s</b>' % problem.problem_name
    op_add_event(physician, new_problem.patient, summary, new_problem)
    activity = "Added <u>problem</u>: <b>%s</b>" % problem.problem_name
    add_problem_activity(new_problem, actor_profile, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@permissions_required(["change_problem_name"])
@login_required
@api_view(["POST"])
def change_name(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    term = request.POST.get('term')
    concept_id = request.POST.get('code', None)

    problem = Problem.objects.get(id=problem_id)
    if Problem.objects.filter(problem_name=term, patient=problem.patient).exists():
        return ajax_response({"msg": "Problem already added"})

    old_problem_concept_id = problem.concept_id
    old_problem_name = problem.problem_name
    if datetime.now() > datetime.strptime(
                            problem.start_date.strftime('%d/%m/%Y') + ' ' + problem.start_time.strftime('%H:%M:%S'),
            "%d/%m/%Y %H:%M:%S") + timedelta(hours=24):
        problem.old_problem_name = old_problem_name

    problem.problem_name = term
    problem.concept_id = concept_id
    problem.save()

    physician = request.user

    if old_problem_concept_id and problem.concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s (%s)</b>' % (
            old_problem_name, old_problem_concept_id, problem.problem_name, problem.concept_id)
    elif old_problem_concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s</b>' % (
            old_problem_name, old_problem_concept_id, problem.problem_name)
    elif problem.concept_id:
        summary = '<b>%s</b> was changed to <b>%s (%s)</b>' % (
            old_problem_name, problem.problem_name, problem.concept_id)
    else:
        summary = '<b>%s</b> was changed to <b>%s</b>' % (old_problem_name, problem.problem_name)

    op_add_event(physician, problem.patient, summary, problem)
    add_problem_activity(problem, actor_profile, summary)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(problem).data

    return ajax_response(resp)


# Problems
@login_required
@api_view(["POST"])
def update_problem_status(request, problem_id):
    resp = {'success': False}

    # Different permissions for different cases
    # Modify this view

    actor_profile = UserProfile.objects.get(user=request.user)

    is_controlled = request.POST.get('is_controlled') == 'true'
    is_active = request.POST.get('is_active') == 'true'
    authenticated = request.POST.get('authenticated') == 'true'

    problem = Problem.objects.select_related("patient").get(id=problem_id)
    problem.is_controlled = is_controlled
    problem.is_active = is_active
    problem.authenticated = authenticated
    problem.save()

    status_labels = {
        'problem_name': problem.problem_name,
        'is_controlled': "controlled" if is_controlled else "not controlled",
        "is_active": "active" if is_active else "not_active",
        "authenticated": "authenticated" if authenticated else "not_authenticated",
    }

    physician = request.user

    summary = """Changed <u>problem</u>: <b>%(problem_name)s</b> status to : <b>%(is_controlled)s</b> ,<b>%(is_active)s</b> ,<b>%(authenticated)s</b>""" % status_labels
    op_add_event(physician, problem.patient, summary, problem)
    activity = summary
    add_problem_activity(problem, actor_profile, activity)

    resp['success'] = True
    return ajax_response(resp)


# Problems
@permissions_required(["modify_problem"])
@login_required
@api_view(["POST"])
def update_start_date(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    start_date = request.POST.get('start_date')
    problem = Problem.objects.get(id=problem_id)
    problem.start_date = get_new_date(start_date)
    problem.save()

    physician = request.user
    patient = problem.patient
    summary = '''Changed <u>problem</u> : <b>%s</b> start date to <b>%s</b>''' % (
        problem.problem_name, problem.start_date)
    op_add_event(physician, patient, summary, problem)
    activity = summary
    add_problem_activity(problem, actor_profile, activity)

    resp['success'] = True
    return ajax_response(resp)


# Add History Note
@permissions_required(["modify_problem"])
@login_required
@api_view(["POST"])
def add_history_note(request, problem_id):
    resp = {'success': False}
    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        return ajax_response(resp)

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    note = request.POST.get('note')
    new_note = ProblemNote.objects.create_history_note(actor_profile, problem, note)

    activity = 'Added History Note  <b>%s</b>' % note
    add_problem_activity(problem, actor_profile, activity, 'input')

    physician = request.user
    patient = problem.patient
    op_add_event(physician, patient, activity, problem)

    resp['success'] = True
    resp['note'] = ProblemNoteSerializer(new_note).data
    return ajax_response(resp)


# Add Wiki Note
@login_required
# @api_view(["POST"])
def add_wiki_note(request, problem_id):
    resp = {'success': False}

    # Check if user is able to view patient
    # Todo
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    note = request.POST.get('note')
    try:
        problem = Problem.objects.get(id=problem_id)
        author = UserProfile.objects.get(user=request.user)
    except (Problem.DoesNotExist, UserProfile.DoesNotExist) as e:
        return ajax_response(resp)

    new_note = ProblemNote.objects.create_wiki_note(author, problem, note)

    activity = 'Added wiki note: <b>%s</b>' % note
    add_problem_activity(problem, actor_profile, activity, 'input')

    physician = request.user
    patient = problem.patient
    op_add_event(physician, patient, activity, problem)

    resp['note'] = ProblemNoteSerializer(new_note).data
    resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def add_patient_note(request, problem_id):
    resp = {'success': False}
    errors = []

    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient
    patient_profile = UserProfile.objects.get(user=patient)

    note = request.POST.get('note')

    if request.user == patient:
        new_note = TextNote(
            author=patient_profile, by='patient', note=note)
        new_note.save()

        problem.notes.add(new_note)

        activity = 'Added patient note'
        add_problem_activity(problem, patient_profile, activity, 'input')

        resp['success'] = True
        resp['note'] = TextNoteSerializer(new_note).data
    else:
        errors.append("Permission Error: Only patient can add patient note.")

    resp['errors'] = errors
    return ajax_response(resp)


# Problems
@login_required
def add_physician_note(request, problem_id):
    # More work required

    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient
    note = request.POST.get('note')

    physician = request.user

    physician_profile = UserProfile.objects.get(user=physician)

    new_note = TextNote(
        author=physician_profile, by='physician', note=note)
    new_note.save()

    problem.notes.add(new_note)

    summary = '''Added <u>note</u> : <b>%s</b> to <u>problem</u> : <b>%s</b>''' % (note, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, physician_profile, activity, 'input')

    new_note_dict = TextNoteSerializer(new_note).data
    resp['note'] = new_note_dict
    resp['success'] = True
    return ajax_response(resp)


# Problems
@permissions_required(["add_goal"])
@login_required
def add_problem_goal(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient

    goal = request.POST.get('name')

    new_goal = Goal(patient=patient, problem=problem, goal=goal)
    new_goal.save()

    physician = request.user

    summary = '''Added <u> goal </u> : <b>%s</b> to <u>problem</u> : <b>%s</b>''' % (goal, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, actor_profile, activity, 'output')

    resp['success'] = True
    resp['goal'] = GoalSerializer(new_goal).data
    return ajax_response(resp)


# Problems
@permissions_required(["add_todo"])
@login_required
def add_problem_todo(request, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    problem.authenticated = actor_profile.role in ['physician', 'admin']
    problem.save()

    patient = problem.patient

    todo = request.POST.get('name')
    due_date = request.POST.get('due_date', None)
    if due_date:
        due_date = parser.parse(due_date, dayfirst=False).date()
        # due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

    new_todo = ToDo(patient=patient, problem=problem, todo=todo, due_date=due_date)

    a1c_id = request.POST.get('a1c_id', None)
    if a1c_id:
        a1c = AOneC.objects.get(id=int(a1c_id))
        new_todo.a1c = a1c

    order = ToDo.objects.all().aggregate(Max('order'))
    if not order['order__max']:
        order = 1
    else:
        order = order['order__max'] + 1
    new_todo.order = order
    new_todo.save()

    colon_cancer_id = request.POST.get('colon_cancer_id', None)
    if colon_cancer_id:
        colon = ColonCancerScreening.objects.get(id=int(colon_cancer_id))
        if not Label.objects.filter(name="screening", css_class="todo-label-yellow", is_all=True).exists():
            label = Label(name="screening", css_class="todo-label-yellow", is_all=True)
            label.save()
        else:
            label = Label.objects.get(name="screening", css_class="todo-label-yellow", is_all=True)
        new_todo.colon_cancer = colon
        new_todo.save()
        new_todo.labels.add(label)

    physician = request.user

    summary = '''Added <u>todo</u> : <a href="#/todo/%s"><b>%s</b></a> to <u>problem</u> : <b>%s</b>''' % (
        new_todo.id, todo, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, actor_profile, activity, 'output')

    summary = '''Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>''' % (
        new_todo.id, new_todo.todo, problem.problem_name)
    op_add_todo_event(physician, patient, summary, new_todo, True)
    # todo activity
    activity = '''
        Added this todo.
    '''
    add_todo_activity(new_todo, actor_profile, activity)

    resp['success'] = True
    resp['todo'] = TodoSerializer(new_todo).data
    return ajax_response(resp)


# Problems
@permissions_required(["add_problem_image"])
@login_required
@api_view(["POST"])
def upload_problem_image(request, problem_id):
    resp = {'success': False}
    actor_profile = UserProfile.objects.get(user=request.user)
    problem = Problem.objects.get(id=problem_id)
    problem.authenticated = actor_profile.role in ['physician', 'admin']
    problem.save()

    patient = problem.patient
    images = request.FILES
    image_holder = []
    for dict in images:
        image = request.FILES[dict]
        patient_image = PatientImage(patient=patient, problem=problem, image=image)
        patient_image.save()

        filename = str(patient_image.image.path)
        img = Image.open(filename)

        if img.mode not in ('L', 'RGB'):
            img = img.convert('RGB')

        img.thumbnail((160, 160), Image.ANTIALIAS)
        img.save(filename)

        activity = summary = '''
        Physician added <u>image</u> to <u>problem</u> <b>%s</b> <br/><a href="/media/%s">
        <img src="/media/%s" class="thumbnail thumbnail-custom" /></a>
        ''' % (problem.problem_name, patient_image.image, patient_image.image)

        op_add_event(request.user, patient, summary, problem)
        add_problem_activity(problem, actor_profile, activity, 'input')

        image_holder.append(patient_image)

    resp['images'] = PatientImageSerializer(image_holder, many=True).data
    resp['success'] = True
    return ajax_response(resp)


# Problems
@permissions_required(["relate_problem"])
@login_required
@api_view(["POST"])
def delete_problem_image(request, problem_id, image_id):
    resp = {'success': False}

    actor_profile = UserProfile.objects.get(user=request.user)
    PatientImage.objects.get(id=image_id).delete()

    problem = Problem.objects.select_related("patient").get(id=problem_id)
    patient = problem.patient
    physician = request.user
    summary = '''Deleted <u>image</u> from <u>problem</u> : <b>%s</b>''' % problem.problem_name
    op_add_event(physician, patient, summary, problem)
    activity = summary
    add_problem_activity(problem, actor_profile, activity, 'input')

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["relate_problem"])
@login_required
@api_view(["POST"])
def relate_problem(request):
    resp = {'success': False}

    actor_profile = UserProfile.objects.get(user=request.user)
    relationship = request.POST.get('relationship') == 'true'
    source_id = request.POST.get('source_id', None)
    target_id = request.POST.get('target_id', None)

    source = Problem.objects.get(id=source_id)
    target = Problem.objects.get(id=target_id)
    activity = None

    if relationship:
        try:
            problem_relationship = ProblemRelationship.objects.get(source=source, target=target)
        except ProblemRelationship.DoesNotExist:
            problem_relationship = ProblemRelationship.objects.create(source=source, target=target)
            activity = '''Created Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (
                source.problem_name, target.problem_name)
    else:
        ProblemRelationship.objects.get(source=source, target=target).delete()
        activity = '''Removed Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (
            source.problem_name, target.problem_name)

    if activity:
        add_problem_activity(source, actor_profile, activity)
        add_problem_activity(target, actor_profile, activity)
        op_add_event(request.user, source.patient, activity)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["modify_problem"])
@login_required
def update_by_ptw(request):
    resp = {'success': False}
    actor_profile = UserProfile.objects.get(user=request.user)

    timeline_data = json.loads(request.body)['timeline_data']
    for problem_json in timeline_data['problems']:
        problem = ProblemService.update_from_timeline_data(problem_json)
        patient = problem.patient
        problem.authenticated = actor_profile.role in ['physician', 'admin']
        problem.save()

        physician = request.user
        summary = '''Changed <u>problem</u> :<b>%s</b> start date to <b>%s</b>''' % (
            problem.problem_name, problem.start_date)
        op_add_event(physician, patient, summary, problem)
        activity = summary
        add_problem_activity(problem, actor_profile, activity)

        resp['success'] = True

    return ajax_response(resp)


@permissions_required(["modify_problem"])
@login_required
def update_state_to_ptw(request):
    resp = {'success': False}
    timeline_data = json.loads(request.body)['timeline_data']
    for problem_json in timeline_data['problems']:
        problem = ProblemService.update_from_timeline_data(problem_json)
        resp['success'] = True
    return ajax_response(resp)


@permissions_required(["set_problem_order"])
@login_required
def update_order(request):
    resp = {'success': False}

    datas = json.loads(request.body)
    if datas.has_key('patient_id'):
        id_problems = datas['problems']
        patient_id = datas['patient_id']
        try:
            problem = ProblemOrder.objects.get(user=request.user, patient_id=patient_id)
        except ProblemOrder.DoesNotExist:
            problem = ProblemOrder(user=request.user, patient_id=patient_id)
            problem.save()

        problem.order = id_problems
        problem.save()

    # list todo
    if datas.has_key('list_id'):
        list_id = datas['list_id']
        labeled_list = LabeledProblemList.objects.get(id=int(list_id))
        labeled_list.problem_list = datas['problems']
        labeled_list.save()

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def new_problem_label(request, problem_id):
    resp = {'success': False, 'status': False, 'new_status': False}

    name = request.POST.get('name')
    css_class = request.POST.get('css_class')

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.filter(name=name, css_class=css_class, author=request.user,
                                        patient=problem.patient).first()
    if not label:
        label = ProblemLabel(name=name, css_class=css_class, author=request.user, patient=problem.patient)
        label.save()
        resp['new_status'] = True
        resp['new_label'] = ProblemLabelSerializer(label).data

    if not label in problem.labels.all():
        problem.labels.add(label)
        resp['status'] = True
        resp['label'] = ProblemLabelSerializer(label).data

    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_problem_labels(request, patient_id, user_id):
    labels = ProblemLabel.objects.filter(patient_id=patient_id, author_id=user_id)
    resp = {
        'labels': ProblemLabelSerializer(labels, many=True).data
    }
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def save_edit_problem_label(request, label_id, patient_id, user_id):
    resp = {'success': False, 'status': False}

    name = request.POST.get('name')
    css_class = request.POST.get('css_class')

    label = ProblemLabel.objects.get(id=label_id)

    if not ProblemLabel.objects.filter(name=name, css_class=css_class, patient_id=patient_id, author_id=user_id):
        label.name = name
        label.css_class = css_class
        label.save()
        resp['status'] = True

    resp['label'] = ProblemLabelSerializer(label).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def add_problem_label(request, label_id, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.get(id=label_id)
    problem.labels.add(label)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def remove_problem_label(request, label_id, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.get(id=label_id)
    problem.labels.remove(label)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def delete_problem_label(request, label_id):
    resp = {'success': False}

    ProblemLabel.objects.get(id=label_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def add_problem_list(request, patient_id, user_id):
    resp = {'success': False}

    data = json.loads(request.body)
    list_name = data['name']
    labels = data['labels']

    problem_labels = ProblemLabel.objects.filter(id__in=[label["id"] for label in labels])
    problems = Problem.objects.filter(labels__in=problem_labels).distinct().order_by('start_date')
    problems_holder = ProblemSerializer(problems, many=True).data
    ProblemService.populate_multiplicity(problems_holder)
    problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)

    labeled_problems = LabeledProblemList.objects.create(user_id=user_id, name=list_name, patient_id=patient_id)
    for label in problem_labels:
        labeled_problems.labels.add(label)
    new_list_dict = LabeledProblemListSerializer(labeled_problems).data
    new_list_dict['problems'] = problems_holder

    resp = {
        'new_list': new_list_dict,
        'success': True
    }
    return ajax_response(resp)


@login_required
def get_label_problem_lists(request, patient_id, user_id):
    resp = {'success': False}

    user = User.objects.get(id=user_id)

    if user.profile.role == 'nurse' or user.profile.role == 'secretary':
        team_members = PhysicianTeam.objects.filter(member=user)
        if team_members:
            user = team_members[0].physician

    lists = LabeledProblemList.objects.filter(user=user, patient_id=patient_id)
    lists_holder = []
    # TODO: To verify the updated logic
    for label_list in lists:
        problem_list = label_list.problem_list
        if problem_list:
            problems_qs = Problem.objects.filter(labels__in=label_list.labels.all()).filter(is_active=True).distinct()
            problems = []
            for problem in problems_qs:
                if problem.id in problem_list:
                    problems.insert(0, problem)
                else:
                    problems.append(problem)
        else:
            problems = Problem.objects.filter(labels__in=label_list.labels.all()).filter(
                is_active=True).distinct().order_by('start_date')

        problems_holder = ProblemSerializer(problems, many=True).data
        if not label_list.problem_list:
            ProblemService.populate_multiplicity(problems_holder)
            problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)

        list_dict = LabeledProblemListSerializer(label_list).data
        list_dict['problems'] = problems_holder
        lists_holder.append(list_dict)

    resp = {
        'problem_lists': lists_holder
    }
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def delete_problem_list(request, list_id):
    resp = {'success': False}

    LabeledProblemList.objects.get(id=list_id).delete()
    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def rename_problem_list(request, list_id):
    resp = {'success': False}

    name = request.POST.get('name')
    LabeledProblemList.objects.filter(id=list_id).update(name=name)

    resp = {'success': True}
    return ajax_response(resp)


@login_required
def get_problems(request, patient_id):
    resp = {'success': False}

    problems = Problem.objects.filter(patient_id=patient_id)

    resp = {
        "problems": ProblemSerializer(problems, many=True).data
    }
    return ajax_response(resp)


@login_required
def get_sharing_problems(request, patient_id, sharing_patient_id):
    resp = {'success': False}

    sharing = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)

    resp = {
        'sharing_problems': ProblemSerializer(sharing.problems.all(), many=True).data,
        'is_my_story_shared': sharing.is_my_story_shared
    }
    return ajax_response(resp)


@login_required
def remove_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    resp = {'success': False}

    sharing_patient = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)
    problem = Problem.objects.get(id=problem_id)
    sharing_patient.problems.remove(problem)

    actor_profile = UserProfile.objects.get(user=request.user)
    activity = "Removed access for patient <b>%s</b> " % sharing_patient.sharing.username
    add_problem_activity(problem, actor_profile, activity)

    resp = {'success': True}
    return ajax_response(resp)


@login_required
def add_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    resp = {'success': False}

    sharing_patient = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)
    problem = Problem.objects.get(id=problem_id)
    sharing_patient.problems.add(problem)

    actor_profile = UserProfile.objects.get(user=request.user)
    activity = "Added access for patient <b>%s</b> " % sharing_patient.sharing.username
    add_problem_activity(problem, actor_profile, activity)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
def update_problem_list_note(request, list_id):
    resp = {'success': False}
    problem_list = LabeledProblemList.objects.get(id=list_id)
    problem_list.note = request.POST.get('note')
    problem_list.save()

    activity = '"%s" was added to the folder "%s"' % (problem_list.note, problem_list.name)
    physician = request.user
    patient = problem_list.patient
    op_add_event(physician, patient, activity)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
def add_new_common_problem(request, staff_id):
    resp = {'success': False}
    problem_name = request.POST.get('problem_name')
    concept_id = request.POST.get('concept_id', None)
    problem_type = request.POST.get('problem_type', None)

    if CommonProblem.objects.filter(concept_id=concept_id, author=request.user).exists():
        resp['msg'] = 'Problem already added'
        return ajax_response(resp)

    problem = CommonProblem(problem_name=problem_name, concept_id=concept_id, author=request.user,
                            problem_type=problem_type)
    problem.save()

    common_problem = CommonProblemSerializer(problem).data
    resp['common_problem'] = common_problem
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
def get_common_problems(request, staff_id):
    resp = {'success': False}

    problems = CommonProblem.objects.filter(author=request.user)
    common_problems = CommonProblemSerializer(problems, many=True).data
    resp['problems'] = common_problems
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
def remove_common_problem(request, problem_id):
    resp = {'success': False}
    problem = CommonProblem.objects.get(id=problem_id)
    if problem.author == request.user:
        problem.delete()
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_data_pins(request, problem_id):
    resp = {'success': False}

    pins = ObservationPinToProblem.objects.filter(problem_id=problem_id)
    observations = [x.observation for x in pins]

    resp['success'] = True
    resp['pins'] = ObservationSerializer(observations, many=True).data
    resp['problem_pins'] = ObservationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)


@login_required
def get_medication_pins(request, problem_id):
    pins = MedicationPinToProblem.objects.filter(problem_id=problem_id)
    resp = {}
    resp['success'] = True
    resp['pins'] = MedicationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)


@permissions_required(["delete_problem"])
@login_required
def delete_problem(request, problem_id):
    resp = {'success': False}

    physician = request.user
    patient_id = request.POST.get('patient_id', None)
    latest_encounter = Encounter.objects.filter(physician=physician,
                                                patient_id=patient_id
                                                ).order_by('-starttime').first()

    if latest_encounter and latest_encounter.stoptime is None:
        resp['success'] = True

        problem = Problem.objects.get(id=problem_id)
        summary = "Deleted <u>problem</u>: <b>%s</b>" % problem.problem_name
        op_add_event(physician, problem.patient, summary)
        problem.delete()

    return ajax_response(resp)


@login_required
def get_related_encounters(request, problem_id):
    resp = {'success': False}
    problem = get_object_or_404(Problem, pk=problem_id)
    encounter_records = problem.problem_encounter_records
    related_encounters = [record.encounter for record in encounter_records.all()]

    resp['encounters'] = EncounterSerializer(related_encounters, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_related_documents(request, problem_id):
    """
    Get document pinned to problem direct or via todo 
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    # Loading problem info
    problem_info = Problem.objects.prefetch_related(
        Prefetch("todo_set", queryset=ToDo.objects.order_by("order"))
    ).get(id=problem_id)

    # Loading document pinned directly to problem
    problem_document_set = problem_info.document_set.all()

    problem_todo_document_set = []
    problem_todo_set = problem_info.todo_set.all()
    for problem_todo in problem_todo_set:
        if problem_todo.document_set.count() != 0:
            problem_todo_document_set += problem_todo.document_set.all()

    document_result_set = set(list(problem_document_set) + list(problem_todo_document_set))

    # Need remove duplicated and sorted by creation date
    resp['documents'] = DocumentSerialization(document_result_set, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_problem_todos(request, problem_id):
    """
    Loading all problem's todos, which todos generated from problem page and todos from pinned medications
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    medication_todo_set = []

    problem_info = get_object_or_404(Problem, pk=problem_id)

    for medication in problem_info.medications.all():
        medication_todo_set += medication.todo_set.all()

    resp['todos'] = TodoSerializer(medication_todo_set + list(problem_info.todo_set.all()), many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_problem_goals(request, problem_id):
    """
    Loading all problem's goals
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    problem_info = get_object_or_404(Problem, pk=problem_id)

    resp['goals'] = GoalSerializer(problem_info.goal_set, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_problem_wikis(request, problem_id):
    """
    Loading all problem's wiki notes
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    history_note = ProblemNote.objects.filter(note_type='history', problem_id=problem_id).order_by(
        '-created_on').first()

    wiki_notes = ProblemNote.objects.filter(note_type='wiki', problem_id=problem_id).order_by('-created_on')
    patient_wiki_notes = [note for note in wiki_notes if note.author.role == "patient"]
    physician_wiki_notes = [note for note in wiki_notes if note.author.role == "physician"]
    other_wiki_notes = [note for note in wiki_notes if note.author.role not in ("patient", "physician")]
    problem_notes = {
        'history': ProblemNoteSerializer(history_note).data,
        'wiki_notes': {
            'patient': ProblemNoteSerializer(patient_wiki_notes, many=True).data,
            'physician': ProblemNoteSerializer(physician_wiki_notes, many=True).data,
            'other': ProblemNoteSerializer(other_wiki_notes, many=True).data
        }
    }

    resp['wiki_notes'] = problem_notes['wiki_notes']
    resp['history_note'] = problem_notes['history']
    resp['success'] = True

    return ajax_response(resp)


@login_required
def get_problem_images(request, problem_id):
    """
    Loading all problem's images
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    problem_images = PatientImage.objects.filter(problem_id=problem_id)

    resp['images'] = PatientImageSerializer(problem_images, many=True).data
    resp['success'] = True

    return ajax_response(resp)
