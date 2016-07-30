DemoTime.DemoState = Backbone.View.extend({
    el: 'body',

    events: {
        'click .demo-changer': 'change_demo_state'
    },

    initialize: function(options) {
        this.options = options;
    },

    // Changing demo state
    change_demo_state: function(event) {
        var self = this,
            link = $(event.target),
            parent = link.parents('li'),
            state = link.data('state'),
            pk = link.data('pk'),
            creator = link.data('creator'),
            url = link.data('url');

        event.preventDefault();

        if (!state || !pk) return false;

        var req = $.ajax({
            url: url,
            method: 'POST',
            data: {
                review: pk,
                reviewer: creator,
                state: state
            }
        });

        req.success(function(msg) {
            if (msg.success) {
                parent.slideUp();
                self.$el.find('#fireworks').fadeIn();
                if ($(window).width() > 720) {
                    self.launch_fireworks();
                    $('#fireworks').click(function() {
                        $(this).hide();
                    });
                }
            }
        });
    },

    launch_fireworks: function() {
        var canvas = document.querySelector('canvas'),
            ctx = canvas.getContext('2d'),
            W = canvas.width = window.innerWidth,
            H = canvas.height = window.innerHeight,
            maxP = 350,
            minP = 100,
            fireworks = [];

        function tick() {
            var newFireworks = [];
            ctx.clearRect(0, 0, W, H);

            fireworks.forEach(function (firework) {
            firework.draw();
            if (!firework.done) newFireworks.push(firework);
            });

            fireworks = newFireworks;
            window.requestAnimationFrame(tick);
        }

        function Vector(x, y) {
            this.x = x;
            this.y = y;
        }

        Vector.prototype = {
            constructor: Vector,

            add: function (vector) {
            this.x += vector.x;
            this.y += vector.y;
            },

            diff: function (vector) {
            var target = this.copy();
            return Math.sqrt(
                (target.x-=vector.x) * target.x + (target.y-=vector.y) * target.y
            );
            },

            copy: function () {
            return new Vector(this.x, this.y);
            }
        };

        var colors = [
            ['rgba(179,255,129,', 'rgba(0,255,0,'], //green / white
            ['rgba(0,0,255,', 'rgba(100,217,255,'], //blue / cyan
            ['rgba(255,0,0,', 'rgba(255,255,0,'], //red / yellow
            ['rgba(145,0,213,', 'rgba(251,144,204,'] //purple / pink
        ];

        function Firework(start, target, speed) {
            this.start = start;
            this.pos = this.start.copy();
            this.target = target;
            this.spread = Math.round(Math.random() * (maxP-minP)) + minP;
            this.distance = target.diff(start);
            this.speed = speed || Math.random() * 5 + 15;
            this.angle = Math.atan2(target.y - start.y, target.x - start.x);
            this.velocity = new Vector(
            Math.cos(this.angle) * this.speed,
            Math.sin(this.angle) * this.speed
            );

            this.particals = [];
            this.prevPositions = [];

            var colorSet = colors[Math.round(Math.random() * (colors.length -1))];

            for (var i=0; i<this.spread; i++) {
            this.particals.push(new Partical(target.copy(), colorSet));
            }
        }

        Firework.prototype = {
            constructor: Firework,

            draw: function () {
            var last = this.prevPositions[this.prevPositions.length -1] || this.pos;

            ctx.beginPath();
            ctx.moveTo(last.x, last.y);
            ctx.lineTo(this.pos.x, this.pos.y);
            ctx.strokeStyle = 'rgba(255,255,255,.7)';
            ctx.stroke();

            this.update();
            },

            update: function () {
            if (this.start.diff(this.pos) >= this.distance) {
                var newParticals = [];
                this.particals.forEach(function (partical) {
                partical.draw();
                if (!partical.done) newParticals.push(partical);
                });

                this.particals = newParticals;
                this.prevPositions = [];

                if (!newParticals.length) this.done = true;
            } else {
                this.prevPositions.push(this.pos.copy());

                if (this.prevPositions.length > 8) {
                this.prevPositions.shift();
                }

                this.pos.add(this.velocity);
            }
            }
        };

        function Partical(pos, colors) {
            this.pos = pos;
            this.ease = 0.2;
            this.speed = Math.random() * 6 + 2;
            this.gravity = Math.random() * 3 + 0.1;
            this.alpha = .8;
            this.angle = Math.random() * (Math.PI*2);
            this.color = colors[Math.round(Math.random() * (colors.length - 1))];
            this.prevPositions = [];
        }

        Partical.prototype = {
            constructor: Partical,

            draw: function () {
            var last = this.prevPositions[this.prevPositions.length -1] || this.pos;

            ctx.beginPath();
            ctx.moveTo(last.x, last.y);
            ctx.lineTo(this.pos.x, this.pos.y);
            ctx.strokeStyle = this.color + this.alpha + ')';
            ctx.stroke();

            this.update();
            },

            update: function () {
            if (this.alpha <= 0) {
                this.done = true;
            } else {
                this.prevPositions.push(this.pos.copy());

                if (this.prevPositions.length > 10) this.prevPositions.shift();
                if (this.speed > 1) this.speed -= this.ease;

                this.alpha -= 0.01;
                this.gravity += 0.01;

                this.pos.add({
                x: Math.cos(this.angle) * this.speed,
                y: Math.sin(this.angle) * this.speed + this.gravity
                });
            }
            }
        };

        function addFirework(target) {
            var startPos = new Vector(W/2, H);
            target = target || new Vector(Math.random() * W, Math.random() * (H - 300));
            fireworks.push(new Firework(startPos, target));
        }

        canvas.addEventListener('click', function (e) {
            addFirework(new Vector(e.clientX, e.clientY))
        }, false);

        function randomFirework() {
            addFirework();
            window.setTimeout(randomFirework, Math.random() * 500);
        }

        tick();
        randomFirework();
    }
});
