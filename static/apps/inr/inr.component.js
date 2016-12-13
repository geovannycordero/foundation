(function () {
    "use strict";

    angular.module('inr', ['ui.bootstrap', 'sharedModule', 'httpModule', 'ngDialog', 'toaster', 'monospaced.elastic'])
        .directive('inr', INR);

    INR.$inject = ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'inrService'];

    function INR(CollapseService, toaster, $location, $timeout, prompt, inrService) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/inr/inr.template.html',
            scope: true,
            link: linkFn
        };

        function linkFn(scope, element, attr, model) {
            // Properties definition
            scope.altInputFormats = ['m/d/yy'];
            scope.format = 'mm/dd/yyyy';

            scope.dateMeasuredDateOptions = {
                initDate: new Date(),
                maxDate: new Date(2100, 5, 22),
                startingDay: 1,
                format: 'mm/dd/yyyy',
                showWeeks: false
            };

            scope.dateMeasuredIsOpened = false;

            scope.nextINRDateOptions = {
                initDate: new Date(),
                maxDate: new Date(2100, 5, 22),
                startingDay: 1,
                format: 'mm/dd/yyyy',
                showWeeks: false
            };

            scope.nextINRIsOpened = false;
            scope.showNoteHistory = false;
            scope.inrInstance = {};                             // This is initialized value for adding new INR item
            scope.orderInstance = {};                           //
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
                inrService.getOrders().then(function (response) {
                    scope.orders = response.data.orders;
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
                        toaster.pop('success', 'Done', 'Load INR table success');
                        scope.inrs = response.data.inrs;
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

                function addINRSuccess() {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new INR success');

                        scope.inrInstance = {};

                        scope.inrs.push(scope.inrInstance);
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
                        // scope.inrs
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

                        // TODO Remove INR row from INR table;
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


            /**
             *
             */
            function addOrder() {
                inrService.addOrder(scope.patientId, scope.orderInstance).then(addOrderSuccess, addOrderFailed);

                function addOrderSuccess() {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new order success');
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