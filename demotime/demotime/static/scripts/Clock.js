// SNAPSVG.JS Clock Layout
var count = 0;
var clock = Snap(".clock");
var frame = clock.circle(32,32,30).attr({
    fill: "#ffffff",
    stroke: "#43B18A",
    strokeWidth: 4
})
var hours = clock.rect(29, 18, 6, 22, 3).attr({fill: "#344d5a"});
var minutes = clock.rect(30, 15, 4, 25, 2).attr({fill: "#344d5a"});
var seconds = clock.path("M30.5,38.625c0,0.828,0.672,1.5,1.5,1.5s1.5-0.672,1.5-1.5c0-0.656-0.414-1.202-1-1.406V10.125c0-0.277-0.223-0.5-0.5-0.5s-0.5,0.223-0.5,0.5v27.094C30.914,37.423,30.5,37.969,30.5,38.625z M31,38.625c0-0.552,0.448-1,1-1s1,0.448,1,1s-0.448,1-1,1S31,39.177,31,38.625z").attr({
    fill: "#43B18A",
});
var middle = clock.circle(32,32,3).attr({
    fill: "#ffffff",
    stroke: "#D91D30",
    strokeWidth: 2
})

// CLOCK Timer

var updateTime = function() {
    var currentTime, data, hour, minute, second;
    currentTime = new Date();
    second = currentTime.getSeconds();
    minute = currentTime.getMinutes();
    hour = currentTime.getHours();
    hour = (hour > 12)? hour -12 : hour;
    hour = (hour == '00')? 12 : hour;
    hour = hour + minute / 60;
    hours.animate({transform: "r" + hour * 30 + "," + 32 + "," + 32}, 200, mina.elastic);
    minutes.animate({transform: "r" + minute * 6 + "," + 32 + "," + 32}, 200, mina.elastic);
    seconds.animate({transform: "r" + second * 6 + "," + 32 + "," + 32}, 500, mina.elastic);
    count = count + 1;

    if (count > 18000) {
        $('.clock').css('opacity', '0.8')
            .css({
                'filter'         : 'blur(1px)',
                '-webkit-filter' : 'blur(1px)',
                '-moz-filter'    : 'blur(1px)',
                '-o-filter'      : 'blur(1px)',
                '-ms-filter'     : 'blur(1px)'
            });
        clearInterval(interval);
    }
}

var interval = setInterval(updateTime, 1000)
function clock() {
    var t = moment(),
        a = t.minutes() * 6,
        o = t.hours() % 12 / 12 * 360 + (a / 12);
    $(".hour").css("transform", "rotate(" + o + "deg)");
    $(".minute").css("transform", "rotate(" + a + "deg)");
}
