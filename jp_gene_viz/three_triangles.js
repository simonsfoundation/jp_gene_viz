/*
* three.js convenience plugin to support surface rendering.
*/

(function (THREE, $) {
    var wireframeMaterial = function (hexcolor) {
        return new THREE.MeshBasicMaterial( { color: hexcolor, wireframe: true } );
    };
    var filledMaterial = function (hexcolor, opacity) {
        var config = { color:hexcolor, shading: THREE.FlatShading };
        if (opacity) {
            config.transparent = true;
            if (opacity < 0) {
                opacity = 0;
            }
            config.opacity = opacity;
        }
        return new THREE.MeshPhongMaterial( config );
    }
    THREE.triangle_surface = function(scene, points, triangle_indices, hexcolor, kind, opacity) {
        // triangles must be oriented correctly!
        debugger;
        var geometry = new THREE.Geometry();
        for (var i=0; i<points.length; i++) {
            var point = points[i];
            var vector = new THREE.Vector3(point[0], point[1], point[2]);
            geometry.vertices.push(vector);
        }
        for (var i=0; i<triangle_indices.length; i++) {
            var t = triangle_indices[i];
            var f = new THREE.Face3(t[0], t[1], t[2]);
            geometry.faces.push(f);
        }
        geometry.computeFaceNormals();
        geometry.computeVertexNormals();
        if (!kind) {
            kind = "solid";
        }
        var material;
        if (kind == "solid") {
            material = filledMaterial(hexcolor, opacity);
        } else if (kind == "wire") {
            material = wireframeMaterial(hexcolor);
        } else {
            throw new Error("unknown triangle surface kind: " + kind);
        }
        material.side = THREE.DoubleSide;
        var mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
        return mesh;
    };
    THREE.triangle_surface.example = function(element) {
        debugger;
        var radius = 500;
        var theta = 0.0;
        var scene = new THREE.Scene();var light = new THREE.DirectionalLight( 0xffaaff );
        light.position.set( 1000, 1000, 1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0x00ffaa );
        light.position.set( 1000, -1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0xaa00ff );
        light.position.set( -1000, 1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0xabcdef);
        light.position.set( -1000, -1000, 1000 );
        scene.add( light );
        light = new THREE.AmbientLight( 0x222222 );
        scene.add(light)
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        camera.position.z = radius;
        var dd = 200;
        var kind = "solid";
        var color = 0x00ff00;
        var opacity = 0.3
        for (var i=0; i<2; i++) {
            var points = [
                [0, 0, 0],
                [dd, 0, 0],
                [0, dd, 0],
                [0, 0, dd]
            ];
            var indices = [
                [0, 1, 2],
                [1, 0, 3],
                [2, 1, 3],
                [0, 2, 3]
            ];
            THREE.triangle_surface(scene, points, indices, color, kind, opacity);
            dd = -200;
            kind = "wire";
            color = 0xff0000;
        }
        // XXXXX temporary
        /*var geometry = new THREE.SphereGeometry( 200, 6, 6 ); 
        var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var sphere = new THREE.Mesh( geometry, material ); 
        scene.add( sphere );*/
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
            requestAnimationFrame(animate);
        };
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        animate();
    };
})(THREE, jQuery);