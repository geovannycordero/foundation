var observations = angular.module('observations', []);

observations.directive('observation', ['observationService', 'toaster', '$location', '$timeout', 'problemService', observationDirective]);

function observationDirective(observationService, toaster, $location, $timeout, problemService) {

    var observationObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/observation.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('observations', function(newVal, oldVal) {
                        if(newVal) {
                            scope.observation = scope.$eval(attr.ngModel);
                            scope.today = moment();
                            if (scope.observation.observation_components.length)
                                scope.a1c_date = moment(scope.observation.observation_components[scope.observation.observation_components.length -1].effective_datetime);

                            if(scope.observation.observation_components.length && scope.observation.todo_past_six_months==false) {
                                scope.last_measurement = scope.observation.observation_components[scope.observation.observation_components.length -1];
                                if (moment() > moment(scope.last_measurement.effective_datetime).add(6, "months")) {
                                    scope.observation.todo_past_six_months = true;
                                    form = {};
                                    form.name = 'A1C order was automatically generated';
                                    form.todo_past_six_months = true;
                                    form.patient_id = scope.patient_id;
                                    form.problem_id = scope.observation.problem.id;
                                    form.observation_id = scope.observation.id;
                                    form.due_date = moment(scope.last_measurement.effective_datetime).add(6, "months").format("YYYY-MM-DD");
                                    problemService.addTodo(form).then(function(data){
                                        scope.problem_todos.push(data['todo']);
                                        scope.observation.observation_todos.push(data['todo']);
                                        toaster.pop('success', 'Done', 'Added Todo!');
                                    });
                                }
                                
                            }

                            scope.set_authentication_false = function() {
                                if (scope.problem) {
                                    if(scope.active_user.role != "physician" && scope.active_user.role != "admin")
                                        scope.problem.authenticated = false;
                                }
                            }

                            scope.repeatThreeMonths = function() {
                                var form = {};
                                form.name = "a1c " + scope.observation.id + " repeats in 3 months";
                                form.patient_id = scope.patient_id;
                                form.problem_id = scope.observation.problem.id;
                                form.observation_id = scope.observation.id;
                                form.due_date = moment().add(3, "months").format("YYYY-MM-DD");
                                problemService.addTodo(form).then(function(data){
                                    scope.problem_todos.push(data['todo']);
                                    scope.observation.observation_todos.push(data['todo']);
                                    toaster.pop('success', 'Done', 'Added Todo!');
                                    scope.set_authentication_false();
                                });
                            }

                            scope.add_note = function(form) {
                                if (form.note == '') return;
                                form.observation_id = scope.observation.id;
                                observationService.addNote(form).then(function(data) {
                                    scope.observation.observation_notes.push(data['note']);
                                    form.note = '';
                                    toaster.pop('success', 'Done', 'Added Note!');
                                });
                            }

                            scope.toggleEditNote = function(note) {
                                note.edit = true;
                            }

                            scope.toggleSaveNote = function(note) {
                                observationService.editNote(note).then(function(data) {
                                    note.edit = false;
                                    toaster.pop('success', 'Done', 'Edited note successfully');
                                });
                            }

                            scope.deleteNote = function(note) {
                                observationService.deleteNote(note).then(function(data){
                                    var index = scope.observation.observation_notes.indexOf(note);
                                    scope.observation.observation_notes.splice(index, 1);
                                    toaster.pop('success', 'Done', 'Deleted note successfully');
                                });
                            }
                        }
                    }, true);
                }
            }

};