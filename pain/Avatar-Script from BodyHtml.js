/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

//Script from Body HTML:
//http://192.210.138.162/patient/2/pain/add_pain_avatar
//Lechicki


$(function () {
    var canvas = document.getElementById("myCanvas");  //store canvas outside event loop
    var isDown = false;     //flag we use to keep track
    var x1, y1, x2, y2;     //to store the coords
    var ctx = document.getElementById("myCanvas").getContext("2d");
    var bodyParts = [{ 'name': 'head part', 'center': [100, 35], 'radius': 30, 'snomed_id': '123850002', 'status': 'gray', 'shape_type': 'circle' },

                     // SPINE

                     { 'name': 'neck structure', 'coordinates': [[90, 70], [110, 70], [110, 90], [90, 90]], 'snomed_id': '45048000', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'structureThoracic spine ', 'coordinates': [[90, 95], [110, 95], [110, 160], [90, 160]], 'snomed_id': '122495006', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Lumbar spine structure', 'coordinates': [[90, 165], [110, 165], [110, 220], [90, 220]], 'snomed_id': '122496007', 'status': 'gray', 'shape_type': 'polygon' },

                    // RIGHT UPPER LIMB

                     { 'name': 'R thorax structure ', 'coordinates': [[40, 95], [85, 95], [85, 135]], 'snomed_id': '51872008', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of right shoulder region', 'center': [30, 110], 'radius': 10, 'snomed_id': '91774008', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Right upper arm structure', 'coordinates': [[20, 125], [40, 125], [40, 178], [20, 178]], 'snomed_id': '368209003', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Right elbow region structure', 'center': [30, 190], 'radius': 8, 'snomed_id': '368149001', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of right forearm', 'coordinates': [[20, 200], [40, 200], [40, 240], [20, 240]], 'snomed_id': '64262003', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of right wrist ', 'center': [30, 252], 'radius': 8, 'snomed_id': '9736006', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of right hand', 'coordinates': [[20, 265], [40, 265], [40, 275], [20, 275]], 'snomed_id': '78791008', 'status': 'gray', 'shape_type': 'polygon' },

                     // R LOWER EXTREMITY

                      { 'name': 'Right hip region structure', 'center': [65, 233], 'radius': 12, 'snomed_id': '287579007', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of right thigh', 'coordinates': [[55, 250], [75, 250], [75, 315], [55, 315]], 'snomed_id': '11207009', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of right knee', 'center': [65, 330], 'radius': 10, 'snomed_id': '6757004', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of right lower leg', 'coordinates': [[55, 345], [75, 345], [75, 395], [55, 395]], 'snomed_id': '32696007', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of right ankle', 'center': [65, 410], 'radius': 10, 'snomed_id': '6685009', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of right foot', 'coordinates': [[55, 425], [75, 425], [75, 440], [55, 440]], 'snomed_id': '7769000', 'status': 'gray', 'shape_type': 'polygon' },

                     // LEFT UPPER LIMB

                     { 'name': 'L thorax structure ', 'coordinates': [[160, 95], [115, 95], [115, 135]], 'snomed_id': '40768004', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of left shoulder region', 'center': [170, 110], 'radius': 10, 'snomed_id': '91775009', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Left upper arm structure', 'coordinates': [[160, 125], [180, 125], [180, 178], [160, 178]], 'snomed_id': '368208006', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Left elbow region structure', 'center': [170, 190], 'radius': 8, 'snomed_id': '368148009', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of left forearm', 'coordinates': [[160, 200], [180, 200], [180, 240], [160, 240]], 'snomed_id': '66480008', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of left wrist ', 'center': [170, 252], 'radius': 8, 'snomed_id': '5951000', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of left hand', 'coordinates': [[160, 265], [180, 265], [180, 275], [160, 275]], 'snomed_id': '85151006', 'status': 'gray', 'shape_type': 'polygon' },

                     // LEFT LOWER LIMB

                     { 'name': 'Left hip region structure', 'center': [135, 233], 'radius': 12, 'snomed_id': '287679003', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of left thigh', 'coordinates': [[125, 250], [145, 250], [145, 315], [125, 315]], 'snomed_id': '61396006', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of left knee', 'center': [135, 330], 'radius': 10, 'snomed_id': '82169009', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of left lower leg', 'coordinates': [[125, 345], [145, 345], [145, 395], [125, 395]], 'snomed_id': '48979004', 'status': 'gray', 'shape_type': 'polygon' },
                     { 'name': 'Structure of left ankle', 'center': [135, 410], 'radius': 10, 'snomed_id': '51636004', 'status': 'gray', 'shape_type': 'circle' },
                     { 'name': 'Structure of left foot', 'coordinates': [[125, 425], [145, 425], [145, 440], [125, 440]], 'snomed_id': '22335008', 'status': 'gray', 'shape_type': 'polygon' },

    ];
    //var cycle = {'gray': 'red', 'red': 'green', 'green': 'gray'};
    var cycle = { 'gray': 'red', 'red': 'gray' };
    function pnpoly(nvert, vertx, verty, testx, testy) {
        var i, j, c = false;
        for (i = 0, j = nvert - 1; i < nvert; j = i++) {
            if (((verty[i] > testy) != (verty[j] > testy)) &&
                (testx < (vertx[j] - vertx[i]) * (testy - verty[i]) / (verty[j] - verty[i]) + vertx[i])) {
                c = !c;
            }
        }
        return c;
    }
    function intersects(x, y, cx, cy, r) {
        var dx = x - cx
        var dy = y - cy
        return dx * dx + dy * dy <= r * r
    }
    function getObject(x, y) {
        for (var i = 0; i < bodyParts.length; i++) {
            var c = bodyParts[i];
            if (c['shape_type'] == 'polygon') {
                var c = bodyParts[i]['coordinates']
                var vertx = [];
                var verty = [];
                for (var j = 0; j < c.length; j++) {
                    vertx.push(c[j][0]);

                }
                for (var j = 0; j < c.length; j++) {
                    verty.push(c[j][1]);

                }

                if (pnpoly(c.length, vertx, verty, x, y) == true) {
                    bodyParts[i]['status'] = cycle[bodyParts[i]['status']];
                    var ctx = document.getElementById("myCanvas").getContext("2d");
                    var c = bodyParts[i];
                    ctx.fillStyle = c['status'];
                    ctx.beginPath();
                    ctx.moveTo(c['coordinates'][0][0], c['coordinates'][0][1]);
                    for (var j = 1; j < c['coordinates'].length; j++) {
                        ctx.lineTo(c['coordinates'][j][0], c['coordinates'][j][1]);
                    }
                    ctx.closePath();
                    ctx.fill();
                }
            } else {
                if (intersects(x, y, c['center'][0], c['center'][1], c['radius']) == true) {
                    bodyParts[i]['status'] = cycle[bodyParts[i]['status']];
                    var ctx = document.getElementById("myCanvas").getContext("2d");
                    ctx.fillStyle = c['status'];
                    ctx.beginPath();
                    ctx.arc(c['center'][0], c['center'][1], c['radius'], 0, 2 * Math.PI, false);

                    ctx.closePath();
                    ctx.fill();
                }
            }
        }
    }
    // get mouse pos relative to canvas (yours is fine, this is just different)
    function getMousePos(canvas, evt) {
        var rect = canvas.getBoundingClientRect();
        return {
            x: evt.clientX - rect.left,
            y: evt.clientY - rect.top
        };
    }
    $(function () {

        for (var i = 0; i < bodyParts.length; i++) {

            var c = bodyParts[i];
            var ctx = document.getElementById("myCanvas").getContext("2d");
            ctx.fillStyle = c['status'];
            ctx.beginPath();
            if (c['shape_type'] == 'polygon') {

                ctx.moveTo(c['coordinates'][0][0], c['coordinates'][0][1]);
                for (var j = 1; j < c['coordinates'].length; j++) {
                    ctx.lineTo(c['coordinates'][j][0], c['coordinates'][j][1]);
                }
            } else {
                ctx.arc(c['center'][0], c['center'][1], c['radius'], 0, 2 * Math.PI, false);
            }
            ctx.closePath();
            ctx.fill();
        }
        $('#myCanvas').on('mousedown', function (e) {
            if (isDown === false) {

                isDown = true;

                var pos = getMousePos(canvas, e);
                x1 = pos.x;
                y1 = pos.y;
            }
        });



        // when mouse button is released (note: window, not canvas here)
        $(window).on('mouseup', function (e) {

            if (isDown === true) {

                var pos = getMousePos(canvas, e);
                x2 = pos.x;
                y3 = pos.y;

                isDown = false;

                //we got two sets of coords, process them
                //alert(x1 + ',' + y1 + ',' +x2 + ',' +y2);
                getObject(x1, y1);
            }
        });


    });
    $('#save').click(function () {
        var json = {};
        for (var i = 0; i < bodyParts.length; i++) {
            json[bodyParts[i]['snomed_id']] = bodyParts[i]['status'];
        }
        json = JSON.stringify(json);
        $.post('/patient/2/pain/add_pain_avatar', { 'json': json }, function () {
            window.location = '/u/patient/manage/2/';
        });
    });
});

