function generateProblemGoalsHtml(problemJson) {
    var problemGoalsHtml = '<ul id="goals_' + problem['problem_id'] +
        '" title="goal_' + problem['problem_id'] + '">';
    goals +=
        '<li><strong>Add:</strong> <input type="text" id="goal_input_' +
        problem['problem_id'] + '" />';
    goals += '<input type="button" value="Submit" parent="' +
        problem['problem_id'] + '" ';
    goals += 'target="goal_input_' + problem['problem_id'] +
        '" object_type="goal" class="submit_data" /></li>';
    for (var j = 0; j < problem['goals'].length; j++) {
        if (problem['goals'][j]['accomplished'] == true) {
            checked = ' checked ';
        } else {
            checked = '';
        }
        if (problem['goals'][j]['is_controlled'] == true) {
            is_controlled_checked = ' checked ';
        } else {
            is_controlled_checked = '';
        }
        notes = '<div id="goal_notes_' + problem['goals'][j]
            ['id'] + '" class="goal_notes">';
        notes += '<strong>Start date:</strong> ' + problem[
            'goals'][j]['start_date'];
        notes +=
            '<br/><label><input type="checkbox" attr="goal" id="' +
            problem['goals'][j]['id'] + '" ' + checked +
            '/></label> ';
        notes +=
            '<strong>Is accomplished</strong><br/><label><input type="checkbox" aswhat="controlled" label="' +
            problem['goals'][j]['goal'] + ' (for probelm ' +
            problem['problem_name'] +
            ')" attr="goal_is_controlled" </label>';
        notes += 'id="' + problem['goals'][j]['id'] + '" ' +
            is_controlled_checked + '/> ';
        notes +=
            '<strong>Currently succeeding</strong><br/><table id="note_' +
            problem['problem_id'] + '">';
        var role =
            "{% if user_role == 'admin' %}physician{% else %}{{ user_role }}{% endif %}";
        current_physician_note = '';
        if (problem['goals'][j]['notes'].length > 0) {
            current_physician_note = problem['goals'][j][
                'notes'
            ][0]['note'];
            console.log(current_physician_note);
            current_physician_note =
                '<strong>Physician note:<br></strong><textarea id="note_input_for_goal_' +
                problem['goals'][j]['id'] + '" value="' +
                current_physician_note + '" cols="50" >' +
                current_physician_note +
                '</textarea><input type="button" value="Submit" parent="' +
                problem['goals'][j]['id'] +
                '" target="note_input_for_goal_' + problem[
                    'goals'][j]['id'] +
                '" object_type="note_for_goal" class="submit_data" />';
        } else {
            current_physician_note =
                '<strong>Physician note:<br></strong><textarea id="note_input_for_goal_' +
                problem['goals'][j]['id'] + '" value="' +
                current_physician_note +
                '" cols="50" /><input type="button" value="Submit" parent="' +
                problem['goals'][j]['id'] +
                '" target="note_input_for_goal_' + problem[
                    'goals'][j]['id'] +
                '" object_type="note_for_goal" class="submit_data" />';
        }
        notes += current_physician_note;
        //notes += '</table></div>';
        goals += '<li id="goal_' + problem['goals'][j]['id'] +
            '" class="' + problem['goals'][j][
                'is_controlled'
            ] + '">' + problem['goals'][j]['goal'] +
            '<input type="button" class="show_goal" value="Show goal" target="goal_notes_' +
            problem['goals'][j]['id'] + '" goal="' +
            problem['goals'][j]['id'] + '" />' + notes +
            '</li>';
    }
    goals += '</ul>';    
    return problemGoalsHtml;
}