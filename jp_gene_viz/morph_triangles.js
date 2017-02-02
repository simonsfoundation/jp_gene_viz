// This module assumes the availability of THREE and jQuery

THREE.morph_triangles = function(morph_triangle_data, scene, duration, material, after_tick) {
    var mesh = null;
    var clock = new THREE.Clock();
    var max_value = morph_triangle_data["max_value"];
    var min_value = morph_triangle_data["min_value"];
    //var epsilon = 1e-7 * (max_value - min_value);
    //var current_t = min_value + epsilon;
    var shift = morph_triangle_data["shift"];
    var scale = morph_triangle_data["scale"];
    var ticking = false;

    var unflatten_list = function(sequence, split_length) {
        var result = []
        for (var i=0; i<sequence.length; i+=split_length) {
            var row = [];
            for (var j=0; j<split_length; j++) {
                row.push(sequence[i + j]);
            }
            result.push(row);
        }
        return result;
    };

    // All coordinates shifted and scaled after input conversion.
    var positions = unflatten_list(morph_triangle_data["positions"], 4);
    var min_position = null;
    var max_position = null;
    for (var i=0; i<positions.length; i++) {
        var position = positions[i];
        for (var j=0; j<4; j++) {
            position[j] = shift[j] + scale[j] * position[j];
            if (min_position != null) {
                if (position[j] < min_position[j]) { min_position[j] = position[j]; }
                if (position[j] > max_position[j]) { max_position[j] = position[j]; }
            }
        }
        if (min_position == null) {
            min_position = position.slice();
            max_position = position.slice();
        }
    }
    var center_position = [];
    for (var j=0; j<4; j++) {
        center_position.push(0.5 * (min_position[j] + max_position[j]));
    }
    var t_extent = (max_value - min_value) * 1.0;
    var epsilon = t_extent * 1e-7;
    var current_t = min_value + epsilon;
    var segments = unflatten_list(morph_triangle_data["segments"], 2);
    var triangles = unflatten_list(morph_triangle_data["triangles"], 3);
    // Compute triangle order and triangle max using calculated positions.
    var triangle_order = [];
    var triangle_max = [];
    for (var i=0; i<triangles.length; i++) {
        var triangle = triangles[i];
        var tr_min = null;
        var tr_max = null;
        for (var j=0; j<triangle.length; j++) {
            var s = segments[triangle[j]];
            var t_low = positions[s[0]][3];
            var t_high = positions[s[1]][3];
            if (t_low < t_high) {
                // NOTE: keep the minimum common extent of all segments
                if (tr_min == null || tr_min < t_low) {
                    tr_min = t_low;
                }
                if (tr_max == null || tr_max > t_high) {
                    tr_max = t_high;
                }
            } else {
                // omit triangles with no time dimension.
                if (t_low > t_high) {
                    throw new Error("segment in triangle has negative time dimension.")
                }
                tr_min = tr_max = null;
                break;
            }
        }
        if (tr_max != null && tr_min!= null && (tr_min < tr_max)) {
            triangle_order.push([tr_min, i]);
            triangle_max.push(tr_max);
        }
    }
    triangle_order.sort(function (a, b) { 
        return a[0] - b[0];
    });
    debugger;
    /*
    var triangle_order = unflatten_list(morph_triangle_data["triangle_order"], 2);
    for (var i=0; i<triangle_order.length; i++) {
        triangle_order[i][0] = triangle_order[i][0];
    }
    var flat_max = morph_triangle_data["triangle_max_t"];
    var triangle_max = {};
    for (var i=0; i<flat_max.length; i+=2) {
        triangle_max[flat_max[i]] = flat_max[i+1];
    }
    */
    var t_units_per_second = t_extent * (1.0 / duration);
    // active interval range
    var min_t = null;
    var max_t = null;
    var transition_start = null;

    var start_transition = function() {
        // cycle to start if past end.
        if (current_t + epsilon > max_value) {
            current_t = min_value;
        }
        min_t = current_t + epsilon;
        max_t = current_t;
        var active_triangles = null;
        current_t = min_t;
        // search for active triangles and determine [min_t, max_t] active interval.
        // XXXX Could optimize this linear scan: binary search for start triangle.
        var last_triangle_order_index = 0;
        // Max t value is the minima of the max triangle values for active triangles.
        while (min_t + epsilon > max_t) {
            if (min_t > max_value) {
                throw new Error("Failed to find morph interval.");
            }
            active_triangles = [];
            max_t = max_value;
            for (var order_index=last_triangle_order_index; order_index<triangle_order.length; order_index++) {
                var order_stat = triangle_order[order_index];
                var triangle_min_t = order_stat[0];
                if (triangle_min_t > min_t) {
                    // Current time interval ends before next triangle enters.
                    if (max_t > triangle_min_t) {
                        max_t = triangle_min_t;
                    }
                    // stop scanning: all other triangles are out of range
                    break;
                }
                last_triangle_order_index = order_index;
                var triangle_index = order_stat[1];
                var triangle_max_t = triangle_max[triangle_index];
                if (triangle_max_t > min_t) {
                    // Current time interval ends before any active triangle exits.
                    if (max_t > triangle_max_t) {
                        max_t = triangle_max_t;
                    }
                    // Triangle is in the active interval.
                    active_triangles.push(triangle_index);
                }
            }
        }
        // Create geometry and morph for transition from min_t to max_t
        var geometry = new THREE.Geometry();
        var geomv = geometry.vertices;
        var geomf = geometry.faces;
        var morphv = [];
        var vertex_index_map = {};
        var interpolate_points_3d = function(p_early, p_late, t_value) {
            var e_t = p_early[3];
            var l_t = p_late[3];
            var ratio = 0.5;
            var diff = l_t - e_t;
            if (diff > epsilon) {
                ratio = (t_value - e_t) * 1.0 / diff;
            }
            if (ratio + epsilon < 0) {
                return p_early;
                //throw new Error("negative segment interpolation " + ratio);
            }
            if (ratio - epsilon > 1) {
                return p_late;
                //throw new Error("over extended segment interpolation " + ratio);
            }
            var interp_3d = []
            for (var i=0; i<3; i++) {
                var interp_i = p_early[i] + ratio * (p_late[i] - p_early[i]);
                interp_3d.push(interp_i);
            }
            return interp_3d;
        }
        var add_segment = function(index) {
            if (index in vertex_index_map) {
                return vertex_index_map[index];
            }
            var segment = segments[index];
            var early = positions[segment[0]];
            var late = positions[segment[1]];
            var vertex_index = geomv.length;
            var start_point = interpolate_points_3d(early, late, min_t);
            var end_point = interpolate_points_3d(early, late, max_t);
            geomv.push(new THREE.Vector3(start_point[0], start_point[1], start_point[2]));
            morphv.push(new THREE.Vector3(end_point[0], end_point[1], end_point[2]));
            vertex_index_map[index] = vertex_index;
            return vertex_index;
        };
        for (var i=0; i<active_triangles.length; i++) {
            var triangle_index = active_triangles[i];
            var tsegments = triangles[triangle_index];
            var vindex = [];
            for (var j=0; j<tsegments.length; j++) {
                vindex.push(add_segment(tsegments[j]));
            }
            var face = new THREE.Face3(vindex[0], vindex[1], vindex[2]);
            geomf.push(face);
        }
        geometry.morphTargets.push( { name: "target0", vertices: morphv } );
        geometry.computeFaceNormals();
        geometry.computeVertexNormals();
        geometry.computeMorphNormals();
        // patch the normals
        var gfaces = geometry.faces;
        var morphNormals = geometry.morphNormals[0];
        var mfaceNormals = morphNormals.faceNormals;
        var mvertexNormals = morphNormals.vertexNormals;
        var patch_if_zero = function (normal, source) {
            if (normal.x == 0 && normal.y == 0 && normal.z == 0) {
                normal.copy(source);
            }
        };
        for (var i = 0; i < gfaces.length; i++) {
            var fnormal = gfaces[i].normal;
            var fvertexNormalsi = gfaces[i].vertexNormals;
            var mvertexNormalsi = mvertexNormals[i];
            patch_if_zero(fnormal, mfaceNormals[i]);
            var mvertexNormalsi = mvertexNormals[i];
            patch_if_zero(fvertexNormalsi[0], mvertexNormalsi.a);
            patch_if_zero(fvertexNormalsi[1], mvertexNormalsi.b);
            patch_if_zero(fvertexNormalsi[2], mvertexNormalsi.c);
        }
        var rotation = null;
        if (mesh != null) {
            rotation = mesh.rotation;
            scene.remove(mesh);
        }
        mesh = new THREE.Mesh( geometry, material );
        if (rotation != null) {
            mesh.rotation.copy(rotation);
        }
        scene.add(mesh);
        transition_start = clock.getElapsedTime();
        return mesh;
    };

    mesh = start_transition();

    var tick = function() {
        var now = clock.getElapsedTime();
        var elapsed = now - transition_start;
        if (elapsed > 0) {
            var influence = elapsed * t_units_per_second / (max_t - min_t);
            if (influence < 1.0) {
                // COMMENTED FOR DEBUG
                mesh.morphTargetInfluences[0] = influence;
                current_t = min_t + (max_t - min_t) * influence;
            } else {
                current_t = max_t;
                start_transition();
            }
        }
        if (after_tick) { after_tick(); }
    };

    var autotick = function() {
        if (ticking) {
            requestAnimationFrame(autotick);
            tick();
        }
    };

    var set_ticking = function(onoff) {
        if ((!ticking) && (onoff)) {
            ticking = true;
            // adjust transition_start to leave influence unchanged
            var now = clock.getElapsedTime();
            var influence = mesh.morphTargetInfluences[0]
            var elapsed = influence * (max_t - min_t) * (1.0 / t_units_per_second);
            transition_start = now - elapsed;
            autotick();
        }
        ticking = onoff;
    };

    var is_ticking = function() {
        return ticking;
    }

    var set_current_time = function(t) {
        // set the current time in input coordinates to t.
        current_t = t;
        if ((current_t < min_t) || (current_t > max_t)) {
            // switch the transition geometry
            start_transition();
        }
        // adjust the clock transition start to reflect the right relative duration.
        var elapsed = (current_t - min_t) * (1.0 / t_units_per_second);
        var now = clock.getElapsedTime();
        transition_start = now - elapsed;
    };

    var get_current_time = function() {
        return current_t;
    };

    var get_mesh = function() {
        return mesh;
    };

    return {
        tick: tick,
        set_ticking: set_ticking,
        is_ticking: is_ticking,
        get_mesh: get_mesh,
        get_current_time: get_current_time,
        set_current_time: set_current_time,
        min: min_position,
        max: max_position,
        center: center_position
    }
};

THREE.morph_triangles.load = function(url, scene, duration, material, after_tick, on_success) {
    var json_success = function(data) {
        var sequence = THREE.morph_triangles(data, scene, duration, material, after_tick);
        if (on_success) {
            on_success(data, sequence);
        }
    }
    jQuery.getJSON(url, json_success);
};

