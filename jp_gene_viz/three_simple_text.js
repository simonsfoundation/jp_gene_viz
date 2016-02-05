/*
* A three.js plugin to make text easier for simple cases.
*/

(function (THREE, $) {
    THREE.simple_text = function (text, position, scene, rotation, options) {
        var settings = $.extend({
            // defaults
            color:  0xeeffff,
            size: 90,
            height: 10,
            bevelThickness: 2,
            bevelSize: 0.5,
            bevelEnabled: true,
            bevelSegments: 3,
            bevelEnabled: true,
            curveSegments: 12,
            steps: 1,
            font:"helvetiker",
            weight: "normal",
        }, options);
        var geometry = new THREE.TextGeometry(text, settings);
        var meshMaterial = new THREE.MeshPhongMaterial({
            specular: 0xffffff,
            color: settings.color,
            shininess: 100,
            metal: true
        });
        //var wirematerial = new THREE.MeshBasicMaterial( { color: 0xff00aa, wireframe: true } );
        var mesh = THREE.SceneUtils.createMultiMaterialObject(geometry, [meshMaterial]);
        mesh.position.x = position[0];
        mesh.position.y = position[1];
        mesh.position.z = position[2];
        if (!rotation) {
            rotation = [0, 0, 0];
        }
        mesh.rotation.x = rotation[0];
        mesh.rotation.y = rotation[1];
        mesh.rotation.z = rotation[2];
        scene.add(mesh);
        return mesh;
    };
    THREE.simple_text.example = function (element) {
        debugger;
        var radius = 1000;
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        camera.position.x = -400;
        camera.position.y = 500;
        camera.position.z = 600;
        camera.lookAt(new THREE.Vector3(100, 100, 100));
        //var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var light = new THREE.DirectionalLight( 0xaaaaff );
        light.position.set( 1000, 1000, 1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0xff00aa );
        light.position.set( 1000, -1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0x00ffaa );
        light.position.set( -1000, 1000, -1000 );
        scene.add( light );
        light = new THREE.AmbientLight( 0x222222 );
        scene.add(light);
        var pi2 = Math.PI/2.0;
        // Add some text to the scene
        THREE.simple_text("x axis", [90, 0, 0], scene);
        THREE.simple_text("y axis", [0, 90, 0], scene, [0, 0, pi2]);
        THREE.simple_text("z axis", [0, 0, 90], scene, [0, -pi2, 0]);
        var renderer = new THREE.WebGLRenderer();
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        renderer.render(scene, camera);
    }
})(THREE, jQuery);