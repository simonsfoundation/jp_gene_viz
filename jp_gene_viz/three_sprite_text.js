/*
* A three.js plugin to make text easier for simple cases using sprites
*/

(function (THREE, $) {
    THREE.sprite_text = function (scene, text, positions, size, fillStyleColor, canvasWidth, options) {
        debugger;
        var settings = $.extend({
            "transparent": true,
            "opacity": 1.0,
            "sizeAttenuation": true,
            "font": "15px Arial",
            "materialColor": 0xffffff,  // ??? not used
            //"textOffset": 4,
        }, options);
        var getTexture = function () {
            // measure the text
            var canvas = document.createElement('canvas');
            canvas.width = canvasWidth;
            canvas.height = canvasWidth;
            var ctx = canvas.getContext('2d');
            ctx.font = settings.font;
            ctx.textBaseline = "middle";
            ctx.textAlign = "center"
            ctx.fillStyle = fillStyleColor;
            var center = canvasWidth * 0.5;
            ctx.fillText(text, center, center);
            // for debug:
            //ctx.beginPath()
            //ctx.strokeStyle = fillStyleColor;
            //ctx.lineWidth = 2;
            //ctx.rect(4, 4, canvasWidth - 8, canvasWidth - 8)
            //ctx.stroke()
            var texture = new THREE.Texture(canvas);
            texture.needsUpdate = true;
            return texture;
        };
        var material = new THREE.PointsMaterial({
            size: size,
            transparent: settings.transparent,
            opacity: settings.opacity,
            map: getTexture(),
            sizeAttenuation: settings.sizeAttenuation,
            color: settings.materialColor
        });
        var geom = new THREE.Geometry();
        for (var i=0; i<positions.length; i++) {
            var position = positions[i];
            var particle = new THREE.Vector3(position[0], position[1], position[2]);
            geom.vertices.push(particle);
        }
        var cloud = new THREE.Points(geom, material);
        cloud.name = 'pointcloud';  // ???
        cloud.sortParticles = true;
        scene.add(cloud);
    };
    THREE.sprite_text.example = function (element) {
        debugger;
        var radius = 1000;
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, 1.0, 1, 100000);
        camera.position.x = 0;
        camera.position.y = -9;
        camera.position.z = -400;
        camera.lookAt(new THREE.Vector3(-90, -90, -10));
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
        THREE.sprite_text(scene, "red x axis", [[90, 0, 0]], 500, "red", 128);
        THREE.sprite_text(scene, "blue y axis", [[0, 90, 0]], 500, "blue", 128);
        THREE.sprite_text(scene, "green z axis", [[0, 0, 90]], 500, "green", 128);
        var renderer = new THREE.WebGLRenderer( {alpha: true});
        renderer.setClearColor(new THREE.Color(0x000000, 1.0));
        renderer.setSize(300, 300);
        element.append(renderer.domElement);
        renderer.render(scene, camera);
    };
})(THREE, jQuery);