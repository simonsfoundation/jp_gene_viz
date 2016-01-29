/*
A three.js plugin to support 3d scatter plots.
*/

(function (THREE, $) {
    // shared objects
    var wireboxGeometry = new THREE.BoxGeometry(2, 2, 2);
    var wireTetrahedronGeometry = new THREE.TetrahedronGeometry();
    wireboxGeometry.shift_origin = -1;
    var wireframeMaterial = function (hexcolor) {
        return new THREE.MeshBasicMaterial( { color: hexcolor, wireframe: true } );
    };
    var openCubeGeometry = (function () {
        var geometry = new THREE.Geometry();
        var p = +1;
        var n = -1;
        var a = new THREE.Vector3(p, p, p);
        var b = new THREE.Vector3(p, p, n);
        var c = new THREE.Vector3(p, n, p);
        var d = new THREE.Vector3(n, n, p);
        var e = new THREE.Vector3(n, p, p);
        var f = new THREE.Vector3(n, p, n);
        var g = new THREE.Vector3(p, n, n);
        var h = new THREE.Vector3(n, n, n);
        var cube = [a, e, d, c, a, b, g, b, f, e, d, h, f, h, g, c];
        for (var i=0; i<cube.length; i++) {
            geometry.vertices.push(cube[i]);
        }
        geometry.shift_origin = 0;
        return geometry;
    })();
    var starGeometry = (function () {
        var geometry = new THREE.Geometry();
        var p = +1;
        var o = new THREE.Vector3(0, 0, 0);
        var xp = new THREE.Vector3(p, 0, 0)
        var xn = xp.clone().negate();
        var yp = new THREE.Vector3(0, p, 0)
        var yn = yp.clone().negate();
        var zp = new THREE.Vector3(0, 0, p)
        var zn = zp.clone().negate();
        var star = [xp, xn, o, yp, yn, o, zp, zn];
        for (var i=0; i<star.length; i++) {
            geometry.vertices.push(star[i]);
        }
        geometry.shift_origin = 0;
        return geometry;
    })();
    var axesGeometry = (function () {
        var geometry = new THREE.Geometry();
        var p = +1;
        var o = new THREE.Vector3(0, 0, 0);
        var xp = new THREE.Vector3(p, 0, 0)
        var yp = new THREE.Vector3(0, p, 0)
        var zp = new THREE.Vector3(0, 0, p)
        var axes= [xp, o, yp, o, zp];
        for (var i=0; i<axes.length; i++) {
            geometry.vertices.push(axes[i]);
        }
        geometry.shift_origin = 0;
        return geometry;
    })();
    var lineMaterial = function (hexcolor) {
        return new THREE.LineBasicMaterial({color: hexcolor});
    };

    THREE.scatter = function(scene, shapeName, centers, scale, hexcolor) {
        var geometry;
        var material;
        if (shapeName == "wireBox") {
            geometry = wireboxGeometry;
            material = wireframeMaterial(hexcolor);
        } else if (shapeName == "openTetrahedron") {
            // XXXX openTetrahedron is not working!!!
            geometry = wireboxGeometry;
            //geometry = wireTetrahedronGeometry;
            material = wireframeMaterial(hexcolor);
        } else if (shapeName == "openCube") {
            geometry = openCubeGeometry;
            material = lineMaterial(hexcolor);
        } else if (shapeName == "star") {
            geometry = starGeometry;
            material = lineMaterial(hexcolor);
        } else if (shapeName == "axes") {
            geometry = axesGeometry;
            material = lineMaterial(hexcolor);
        } else {
            throw "Unknown shape name for scatter " + shapeName;
        }
        for (var i=0; i<centers.length; i++) {
            var center = centers[i];
            var mesh;
            if (shapeName == "openCube" || shapeName == "star" || shapeName == "axes") {
                mesh = new THREE.Line(geometry, material);
            } else {
                mesh = new THREE.Mesh(geometry, material);
            }
            var shift = geometry.shift_origin;
            mesh.position.x = center[0] + shift;
            mesh.position.y = center[1] + shift;
            mesh.position.z = center[2] + shift;
            mesh.scale.x = scale;
            mesh.scale.y = scale;
            mesh.scale.z = scale;
            scene.add(mesh)
        }
        return mesh;
    };
    THREE.scatter.example = function(element, shapeName) {
        debugger;
        if (!shapeName) {
            shapeName = "wireBox";
        }
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
        THREE.scatter(scene, shapeName, centers, 30.0, 0x00ff00);
        var renderer = new THREE.WebGLRenderer();
        var animate = function() {
            theta += 0.01;
            camera.position.x = radius * Math.sin(theta);
            camera.position.y = radius * Math.sin(theta);
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
