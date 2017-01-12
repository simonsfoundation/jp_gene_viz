/*
A three.js plugin to support rotation
*/

(function (THREE, $) {
    THREE.orbiter = function (camera, renderer, scene, options) {
        debugger;
        var settings = $.extend({
            "autoRotate": true,
            "do_rotation": true,
            "center": scene.position.clone(),
            //"offset": {"x": 0.0, "y": 0.0, "z": 1},
        }, options);

        var orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
        orbitControls.autoRotate = settings.autoRotate;
        var center = settings.center;
        if (Array.isArray(center)) {
            center = new THREE.Vector3(center[0], center[1], center[2]);
        }
        orbitControls.center = center;
        camera.lookAt(center);

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
        camera.position.z = -500;
        var geometry = new THREE.SphereGeometry( 100, 16, 16 ); 
        //var material = new THREE.MeshBasicMaterial( {color: 0xffff00, wireframe:true} ); 
        var material =  new THREE.MeshPhongMaterial( { color:0xffffff, shading: THREE.FlatShading } );
        var light = new THREE.DirectionalLight( 0xaaaaff );
        light.position.set( 1000, 1000, 0 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0xff00aa );
        light.position.set( 1000, 1000, -1000 );
        scene.add( light );
        light = new THREE.DirectionalLight( 0x00ffaa );
        light.position.set( -1000, 1000, -1000 );
        scene.add( light );
        light = new THREE.AmbientLight( 0x222222 );
        scene.add(light)
        var cx = 22500;
        var cy = -1250;
        var cz = 6125;
        camera.position.x = cx;
        camera.position.y = cy-100;
        camera.position.z = cz-500;
        var center = new THREE.Vector3(cx, cy, cz);
        var off = 250;
        for (var i=-1; i<2; i+=2) {
            for (var j=-1; j<2; j+=2) {
                for (var k=-1; k<2; k+=2) {
                    var sphere = new THREE.Mesh( geometry, material );
                    sphere.position.x = cx + i * off;
                    sphere.position.y = cy + j * off/2;
                    sphere.position.z = cz + k * off/3;
                    scene.add( sphere );
                }
            }
        }
        var renderer = new THREE.WebGLRenderer();
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        camera.lookAt(center);
        renderer.render(scene, camera);
        var options = {"center": center}
        var orbiter = THREE.orbiter(camera, renderer, scene, options);
        return orbiter;
    }
})(THREE, jQuery);
