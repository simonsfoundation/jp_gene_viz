/*
A three.js plugin to support rotation
*/

(function (THREE, $) {
    THREE.rotator = function (gamma, delta, radius, camera, renderer, scene, options) {
        debugger;
        var settings = $.extend({
            "center": scene.position,
            "dtheta": 0.001,
            "theta": 0,
            "delta": delta,
            "gamma": gamma,
            "radius": radius,
            "do_rotation": true,
            //"offset": {"x": 0.0, "y": 0.0, "z": 1},
        }, options);
        var animate = function () {
            settings.theta += settings.dtheta;
            var s = Math.sin(settings.theta);
            var c = Math.cos(settings.theta);
            var g = settings.gamma;
            var d = settings.delta;
            var r = settings.radius;
            var o = settings.center;
            var camera_coordinate = function(cname) {
                camera.position[cname] = o[cname] + r * (c * g[cname] + s * d[cname]);
            }
            camera_coordinate("x");
            camera_coordinate("y");
            camera_coordinate("z");
            camera.lookAt(settings.center);
            if (settings.do_rotation) {
                requestAnimationFrame(animate);
            }
            // render after requesting animation in case render is slow.
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
    THREE.rotator.example = function(element) {
        debugger;
        var radius = 1000;
        var theta = 0.0;
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        var geometry = new THREE.SphereGeometry( 300, 16, 16 ); 
        //var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var material =  new THREE.MeshPhongMaterial( { color:0xffffff, shading: THREE.FlatShading } );
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
        renderer.render(scene, camera);
        var rotator = THREE.rotator(gamma, delta, radius, camera, renderer, scene);
        return rotator;
    }
})(THREE, jQuery);
