(function () {
    "use strict";

    angular.module('inr', ['ui.bootstrap', 'sharedModule', 'xeditable', 'angular-spinkit',
        'httpModule', 'ngDialog', 'toaster', 'monospaced.elastic'])
        .directive('inr', INR);

    INR.$inject = ['uibDateParser', 'toaster', '$location', '$timeout', '$filter', 'inrService'];

    function INR(uibDateParser, toaster, $location, $timeout, $filter, inrService) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/inr/inr.template.html',
            scope: true,
            link: linkFn
        };

        function linkFn(scope, element, attr, model) {
            var now = new Date();

            // Properties definition
            scope.altInputFormats = ['M/d/yy'];
            scope.editEnabled = [];
            scope.format = 'MM/dd/yyyy';
            scope.dateMeasuredDateOptions = {
                initDate: new Date(),
                maxDate: new Date(2100, 5, 22),
                startingDay: 1,
                format: 'MM/dd/yyyy',
                showWeeks: false
            };
            scope.dateMeasuredIsOpened = false;
            scope.nextINRDateOptions = {
                initDate: new Date(),
                maxDate: new Date(2100, 5, 22),
                startingDay: 1,
                format: 'MM/dd/yyyy',
                showWeeks: false
            };
            scope.nextINRIsOpened = false;
            scope.showNoteHistory = false;
            scope.inrInstance = {
                date_measured: now, // current date
                next_inr: new Date(now.getFullYear(), now.getMonth() + 1, now.getDate())// one month later current date
            };
            scope.todoName = "";                           //
            scope.noteInstance = {};                            //
            scope.totalNote = 0;
            scope.patientId = $('#patient_id').val();           // TODO: Need to be make an other way to retrieve patient ID

            scope.inrTarget = null;                             // Goal(Target INR for the patient. Only one option is selected) 2-3 or 2.5-3.5.
            scope.inrs = [];                                    // Data for INR table
            scope.medications = [];                             // Data for medication list
            scope.problems = [];                                // Data for problem list
            scope.orders = [];                                // Data for problem list
            scope.noteHistories = [];

            // Method definition (aka widget's behaviour)
            scope.updateTargetINR = updateTargetINR;
            scope.addINR = addINR;
            scope.loadINRs = loadINRs;
            scope.editINR = editINR;
            scope.deleteINR = deleteINR;
            scope.showAllINRTable = showAllINRTable;
            scope.addOrder = addOrder;
            scope.updateNote = updateNote;
            scope.showAllNotes = showAllNotes;
            scope.hideAllNotes = hideAllNotes;

            // Bootstrap load the widget's data
            initData();

            /**
             * Function to load all related data for this widget
             */
            function initData() {
                // Get current target INR setting.
                inrService.getINRTarget(scope.patientId).then(function (response) {
                    scope.inrTarget = response.data.target;
                });

                // Load INR table(5 latest table value is loaded)
                scope.loadINRs(5);

                // Load related problem
                inrService.getProblems(scope.patientId).then(function (response) {
                    scope.problems = response.data.problems;
                });

                // Load related medicine
                inrService.getMedications(scope.patientId).then(function (response) {
                    scope.medications = response.data.medications;
                });

                // Load all orders(aka todo) generated by this INR widget
                inrService.getOrders(scope.patientId).then(function (response) {
                    scope.orders = response.data.orders;
                    scope.todos_ready = true;
                });

                // Load quick glance of text note was added to this INR widget(latest text note info & Total count of text note added)
                inrService.loadNotes(scope.patientId, 1).then(function (response) {
                    scope.noteInstance = response.data.note;
                    scope.totalNote = response.data.total;
                });
            }

            /**
             * Handler for set INR target
             */
            function updateTargetINR() {
                inrService.setINRTarget(scope.patientId, scope.inrTarget).then(updateTargetINRSuccess, updateTargetINRFailed);

                function updateTargetINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Update Target INR success');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }

                function updateTargetINRFailed(response) {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            }


            /**
             *
             * @param rows : 0 for loading all item
             */
            function loadINRs(rows) {
                inrService.getINRs(scope.patientId, rows).then(getINRsSuccess, getINRsFailed);

                function getINRsSuccess(response) {
                    if (response.data.success) {
                        scope.inrs = response.data.inrs;
                        _.map(scope.inrs, function (item, key) {
                            item.date_measured = uibDateParser.parse(item.date_measured, 'MM/dd/yyyy');
                            item.next_inr = uibDateParser.parse(item.next_inr, 'MM/dd/yyyy');
                        });

                        scope.inrInstance.current_dose = _.first(response.data.inrs).current_dose;
                        scope.inrInstance.inr_value = _.first(response.data.inrs).inr_value;
                        scope.inrInstance.new_dosage = _.first(response.data.inrs).new_dosage;
                    } else {
                        toaster.pop('error', 'Error', 'Load INR table failed!');
                    }
                }

                function getINRsFailed() {
                    toaster.pop('error', 'Error', 'Load INR table failed!');
                }
            }

            /**
             * Allow adding new INR to INR table
             * Refer: https://trello.com/c/RPmWI84X
             */
            function addINR() {
                inrService.addINR(scope.patientId, scope.inrInstance).then(addINRSuccess, addINRError);

                function addINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new INR success');

                        scope.inrs.unshift(response.data.inr);

                        // Should not change becuz it will prepopulated data
                        // scope.inrInstance = {};
                    } else {
                        toaster.pop('error', 'Error', 'Add INR failed');
                    }

                }

                function addINRError() {
                    toaster.pop('error', 'Error', 'Add INR failed');
                }
            }

            /**
             * Refer: https://trello.com/c/zjh8RsMk
             * @param inr
             */
            function editINR(inr) {
                inrService.updateINR(scope.patientId, inr).then(editINRSuccess, editINRFailed);

                function editINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Msg when success');

                        // TODO Update INR row from INR table;
                        var index = scope.inrs.indexOf(inr);
                        scope.editEnabled[index] = false;
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }

                function editINRFailed(response) {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            }

            /**
             * https://trello.com/c/zjh8RsMk
             * @param inr
             */
            function deleteINR(inr) {
                inrService.deleteINR(scope.patientId, inr).then(deleteINRSuccess, deleteINRFailed);

                function deleteINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'INR value deleted successfully');

                        var index = scope.inrs.indexOf(inr);
                        scope.inrs.splice(index, 1);

                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }

                function deleteINRFailed(response) {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            }

            /**
             * Load all INR value which is related to this INR
             */
            function showAllINRTable() {
                scope.loadINRs(0);
            }


            /***
             *
             * @param title: todo name
             * @param repeat: 1 - 1 month, 2 - 1 week, 3- 2 weeks
             */
            function addOrder(title, repeat) {
                // Manipulate due date before submmiting
                var now = new Date();
                switch (repeat) {
                    case 1: // Repeat 1 month
                        var due_date = new Date(now.getFullYear(), now.getMonth() + 1, now.getDate());
                        break;
                    case 2: // Repeat 1 week
                        var due_date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 7);
                        break;
                    case 3: // Repeat 2 weeks
                        var due_date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 14);
                        break;
                }

                if (due_date != null) {
                    due_date = $filter('date')(due_date, 'yyyy-MM-dd');
                }

                inrService.addOrder(scope.patientId, {
                    'todo': title,
                    'due_date': due_date
                }).then(addOrderSuccess, addOrderFailed);

                function addOrderSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new order success');
                        scope.orders.push(response.data.order);
                        scope.todoName = "";
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }

                function addOrderFailed() {
                    toaster.pop('error', 'Error', 'Add order failed!');

                }

            }

            /**
             * Handler when the text note is changed
             */
            function updateNote() {
                inrService.addNote(scope.patientId, scope.noteInstance).then(updateNoteSuccess, updateNoteFailed);
                function updateNoteSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Update note success');
                        scope.noteInstance = response.data.note;
                        scope.totalNote = response.data.total;
                    } else {
                        toaster.pop('error', 'Error', 'Update note failed!');
                    }
                }

                function updateNoteFailed(response) {
                    toaster.pop('error', 'Error', 'Update note failed!');
                }
            }

            /**
             * Loading all old note history
             */
            function showAllNotes() {
                // Toggle flag
                scope.showNoteHistory = true;

                // Load all notes
                inrService.loadNotes(scope.patientId, 0).then(showAllNoteSuccess, showAllNoteFailed);

                function showAllNoteSuccess(response) {
                    if (response.data.success) {
                        scope.noteHistories = response.data.notes;
                    } else {
                        toaster.pop('error', 'Error', 'Loading note history failed!');
                    }
                }

                function showAllNoteFailed(response) {
                    toaster.pop('error', 'Error', 'Loading note history failed!');

                }
            }

            function hideAllNotes() {
                scope.showNoteHistory = false;

            }
        }
    }
})();