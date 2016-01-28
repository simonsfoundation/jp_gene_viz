/*
A three.js plugin to support 3d scatter plots.
*/

(function (THREE, $) {
    // shared objects
    var wireboxGeometry = new THREE.BoxGeometry(2, 2, 2);
    wireboxGeometry.shift_origin = -1;
    var wireframeMaterial = function (hexcolor) {
        return new THREE.MeshBasicMaterial( { color: hexcolor, wireframe: true } );
    };
    THREE.scatter = function(scene, shapeName, centers, scale, hexcolor) {
        var geometry;
        var material;
        if (shapeName == "wirebox") {
            geometry = wireboxGeometry;
            material = wireframeMaterial(hexcolor);
        } else {
            throw "Unknown shape name for scatter " + shapeName;
        }
        for (var i=0; i<centers.length; i++) {
            var center = centers[i];
            var mesh = new THREE.Mesh(geometry, material);
            var shift = geometry.shift_origin;
            mesh.position.x = center[0] + shift;
            mesh.position.y = center[1] + shift;
            mesh.position.z = center[2] + shift;
            mesh.scale.x = scale;
            mesh.scale.y = scale;
            mesh.scale.z = scale;
            scene.add(mesh)
        }
    };
    THREE.scatter.example = function(element) {
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
            centers.push([Math.sin(angle) * 150, Math.cos(angle) * 200, i * 10])
        }
        THREE.scatter(scene, "wirebox", centers, 20.0, 0x00ff00);
        var renderer = new THREE.WebGLRenderer();
        var animate = function() {
            theta += 0.01;
            camera.position.x = radius * Math.sin(theta);
            //camera.position.y = radius * Math.sin(theta);
            camera.position.z = radius * Math.cos(theta);
            camera.lookAt(scene.position);
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        };
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        animate();
    };
})(THREE, jQuery);
