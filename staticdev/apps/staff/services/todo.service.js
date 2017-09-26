(function () {

    'use strict';

    angular.module('StaffApp').service('todoService',
        function ($http, $q, $cookies, httpService) {
            return {
                csrf_token: csrf_token,
                fetchTodoInfo: fetchTodoInfo,
                addComment: addComment,
                editComment: editComment,
                deleteComment: deleteComment,
                changeTodoText: changeTodoText,
                changeTodoDueDate: changeTodoDueDate,
                addTodoLabel: addTodoLabel,
                removeTodoLabel: removeTodoLabel,
                saveCreateLabel: saveCreateLabel,
                saveEditLabel: saveEditLabel,
                deleteLabel: deleteLabel,
                addTodoAccessEncounter: addTodoAccessEncounter,
                addAttachment: addAttachment,
                deleteAttachment: deleteAttachment,
                getTodoActivity: getTodoActivity,
                fetchTodoMembers: fetchTodoMembers,
                addTodoMember: addTodoMember,
                removeTodoMember: removeTodoMember,
                fetchLabels: fetchLabels,
                updateTodoOrder: updateTodoOrder,
                updateTodoStatus: updateTodoStatus
            };

            function csrf_token() {

                return $cookies.get('csrftoken');
            }

            function fetchTodoInfo(todo_id) {
                let url = `/todo/todo/${todo_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function addComment(form) {
                let url = `/todo/todo/${form.todo_id}/comment`;

                return httpService.post(form, url);
            }

            function editComment(form) {
                let url = `/todo/todo/${form.id}/edit`;

                return httpService.post(form, url);
            }

            function deleteComment(form) {
                let url = `/todo/todo/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function changeTodoText(form) {
                let url = `/todo/todo/${form.id}/changeText`;

                return httpService.post(form, url);
            }

            function changeTodoDueDate(form) {
                let url = `/todo/todo/${form.id}/changeDueDate`;

                return httpService.post(form, url);
            }

            function addTodoLabel(id, todo_id) {
                let form = {};
                let url = `/todo/todo/${id}/${todo_id}/addLabel`;

                return httpService.post(form, url);
            }

            function removeTodoLabel(id, todo_id) {
                let form = {};
                let url = `/todo/todo/removeLabel/${id}/${todo_id}`;

                return httpService.post(form, url);
            }

            function saveCreateLabel(todo_id, form) {
                let url = `/todo/todo/newLabel/${todo_id}`;

                return httpService.post(form, url);
            }

            function saveEditLabel(form) {
                let url = `/todo/todo/saveEditLabel/${form.id}`;

                return httpService.post(form, url);
            }

            function deleteLabel(form) {
                let url = `/todo/todo/deleteLabel/${form.id}`;

                return httpService.post(form, url);
            }

            function addTodoAccessEncounter(id) {
                let form = {};
                let url = `/todo/todo/accessEncounter/${id}`;

                return httpService.post(form, url);
            }

            function addAttachment(form, file) {
                let deferred = $q.defer();

                let uploadUrl = `/todo/todo/${form.todo_id}/addAttachment`;

                let fd = new FormData();

                fd.append('csrfmiddlewaretoken', this.csrf_token());

                fd.append(0, file);


                $http.post(uploadUrl, fd, {
                    transformRequest: angular.identity,
                    headers: {'Content-Type': undefined}
                })
                    .success(function (data) {
                        deferred.resolve(data);
                    })
                    .error(function (data) {
                        deferred.resolve(data);

                    });

                return deferred.promise;
            }

            function deleteAttachment(form) {
                let url = `/todo/attachment/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function getTodoActivity(todo_id, last_id) {
                let params = {};
                let url = `/todo/todo/${todo_id}/${last_id}/activity/`;
                return httpService.get(params, url);
            }

            function fetchTodoMembers(user_id) {
                let params = {};
                let url = `/u/members/${user_id}/getlist/`;
                return httpService.get(params, url);
            }

            function addTodoMember(form, member) {
                let url = `/todo/todo/${form.id}/addMember`;

                return httpService.post(member, url);
            }

            function removeTodoMember(form, member) {
                let url = `/todo/todo/${form.id}/removeMember`;

                return httpService.post(member, url);
            }

            function fetchLabels(user_id) {
                let params = {};
                let url = `/todo/todo/${user_id}/getlabels`;
                return httpService.get(params, url);
            }

            function updateTodoOrder(form) {
                let url = '/todo/todo/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updateTodoStatus(form) {
                let url = `/todo/todo/${form.id}/update/`;
                return httpService.post(form, url);
            }
        });

})();