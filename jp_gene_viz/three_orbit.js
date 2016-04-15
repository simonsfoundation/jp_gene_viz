/*
A three.js plugin to support rotation
*/

(function (THREE, $) {
    THREE.orbiter = function (camera, renderer, scene, options) {
        debugger;
        var settings = $.extend({
            "autoRotate": true,
            "do_rotation": true,
            "center": scene.position,
            //"offset": {"x": 0.0, "y": 0.0, "z": 1},
        }, options);

        var orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
        orbitControls.autoRotate = settings.autoRotate;
        orbitControls.center = settings.center;

        var clock = new THREE.Clock();

        var animate = function () {
            //sphere.rotation.y=step+=0.01;
            var delta = clock.getDelta();
            orbitControls.update(delta);

            // render using requestAnimationFrame
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        };
        settings.go = function () {
            if (!settings.do_rotation) {
                settings.do_rotation = true;
                animate();
            };
        };
        settings.stop = function () {
            settings.do_rotation = false;
        };
        settings.destroy = function () {
            debugger;
            // release all references
            settings = {};
            settings.do_rotation = false;
        }
        if (settings.do_rotation) {
            animate();
        }
        return settings;
    };
    THREE.orbiter.example = function(element) {
        debugger;
        var radius = 1000;
        var theta = 0.0;
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        var geometry = new THREE.SphereGeometry( 300, 16, 16 ); 
        //var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var material =  new THREE.MeshPhongMaterial( { color:0xffffff, shading: THREE.FlatShading } );
        var light = new THREE.DirectionalLight( 0xaaaaff );
        light.position.set( -1000, -1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0xff00aa );
        light.position.set( 1000, -1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0x00ffaa );
        light.position.set( -1000, 1000, -1000 );
        scene.add( light );
        light = new THREE.AmbientLight( 0x222222 );
        scene.add(light)
        var sphere = new THREE.Mesh( geometry, material );
        sphere.position.x = 140; // put it off center a bit.
        scene.position.y = 3000;
        scene.add( sphere );
        var s2 = Math.sqrt(2.0)/2.0;
        var gamma = {"x": 0, "y": 0, "z": 1};
        var delta = {"x": s2, "y": s2, "z": 0};
        var radius = 1000;
        var renderer = new THREE.WebGLRenderer();
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        camera.lookAt(scene.position);
        renderer.render(scene, camera);
        var orbiter = THREE.orbiter(camera, renderer, scene);
        return orbiter;
    }
})(THREE, jQuery);
