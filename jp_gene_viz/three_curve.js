/*
* three.js plugin to support curve drawing.
*/

(function (THREE, $) {
    var lineMaterial = function (hexcolor) {
        return new THREE.LineBasicMaterial({color: hexcolor});
    };
    THREE.simple_curve = function(scene, points, hexcolor) {
        debugger;
        var geometry = new THREE.Geometry();
        for (var i=0; i<points.length; i++) {
            var point = points[i];
            var vector = new THREE.Vector3(point[0], point[1], point[2]);
            geometry.vertices.push(vector);
        }
        var material = lineMaterial(hexcolor);
        var mesh = new THREE.Line(geometry, material);
        scene.add(mesh);
        return mesh;
    };
    var clearScene = function(obj, scene) {
        if (obj instanceof THREE.Mesh)
        {
            obj.geometry.dispose();
            obj.geometry = null;
            obj.material.dispose();
            obj.material = null;
            if (obj.dispose) {
                obj.dispose(); // required in r69dev to remove references from the renderer.
            }
            if (scene) {
                scene.remove(obj);
            }
            obj = null;
        }
        else
        {
            if (obj.children) {
                while (obj.children.length > 0) {
                    clearScene(obj.children[0]);
                    obj.remove(obj.children[0]);
                }
            }
        }
    }
    // XXXX This is a general "remove all" function... probably should be in another module?
    THREE.simple_curve.dispose_all = function(obj, scene) {
        // based on http://stackoverflow.com/questions/25126352/deallocating-buffergeometry
        clearScene(obj, scene);
    }
    THREE.simple_curve.example = function(element, limit) {
        debugger;
        var radius = 1000;
        var theta = 0.0;
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        camera.position.z = radius;
        var centers = []
        var d_angle = Math.PI / 9.0
        for (var i=0; i<15; i++) {
            var angle = i * d_angle
            centers.push([Math.sin(angle) * 350, Math.cos(angle) * 200, i * 10])
        }
        THREE.simple_curve(scene, centers, 0x00ff00);
        // XXXXX temporary
        var geometry = new THREE.SphereGeometry( 200, 6, 6 ); 
        var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var sphere = new THREE.Mesh( geometry, material ); 
        scene.add( sphere );
        var renderer = new THREE.WebGLRenderer();
        var count = 0;
        var animate = function() {
            count += 1;
            theta += 0.01;
            camera.position.x = radius * Math.sin(theta);
            camera.position.y = radius * Math.sin(theta);
            camera.position.z = radius * Math.cos(theta);
            camera.lookAt(scene.position);
            renderer.render(scene, camera);
            if ((limit) && (count > limit)) {
                THREE.simple_curve.dispose_all(scene);
                alert("limit exceeded: animation stopped, scene cleared.")
                renderer.render(scene, camera)
            } else {
                requestAnimationFrame(animate);
            }
        };
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        animate();
    };
})(THREE, jQuery);