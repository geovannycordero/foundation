(function(){

	'use strict';

	angular.module('StaffApp').service('staffService',
		function( $q,$cookies, $http, httpService){

		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};

		this.fetchActiveUser = function(){
			var params = {};
			var url = '/u/active/user/';
			return httpService.get(params, url);
		};

		this.getPatientsList = function(){
			var form = {};
			var url = '/u/patients/';
			return httpService.post(form, url);
		};

		this.getUserTodoList = function(user_id){
			var form = {};
			var url = '/todo/todo/user_todos/' + user_id;
			return httpService.post(form, url);
		};

		this.addToDo = function(form){
			var url = '/todo/staff/'+form.user_id+'/todos/add/new_todo';
			return httpService.post(form, url);
		};

		this.addToDoList = function(form){
			var url = '/todo/staff/'+form.user_id+'/new_list';
			return httpService.postJson(form, url);
		};

		this.fetchLabeledTodoList = function(user_id){
			var params = {};
			var url ='/todo/todo/'+user_id+'/getLabeledTodoList';
			return httpService.get(params, url);
		};

		this.deleteToDoList = function(form){
			var url = '/todo/todo/'+form.id+'/deleteTodoList';
			return httpService.post(form, url);
		};

	});

})();