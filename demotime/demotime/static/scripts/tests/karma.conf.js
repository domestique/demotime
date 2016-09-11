// Karma configuration
// Generated on Mon Jul 11 2016 20:13:22 GMT-0400 (EDT)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],

    // list of files / patterns to load in the browser
    files: [
        { pattern: '../library/jquery-2.1.3.min.js', watched: false },
        { pattern: '../library/js.cookie.js', watched: false },
        { pattern: '../library/jquery.tooltipster.min.js', watched: false },
        { pattern: '../library/swal.js', watched: false },
        { pattern: '../library/snap.svg-min.js', watched: false },
        { pattern: '../library/mousetrap.js', watched: false },
        { pattern: '../library/underscore.js', watched: false },
        { pattern: '../library/backbone.js', watched: false },
        { pattern: '../library/wysiwyg.min.js', watched: false },
        { pattern: '../library/wysiwyg.editor.min.js', watched: false },
        { pattern: '../library/fireworks.js', watched: false },
        { pattern: '../library/selects.js', watched: false },
        { pattern: '../library/sticky.kit.min.js', watched: false },
        '../DemoTime.js',
        '../*.js',
        'spec/*.js'
    ],

    // list of files to exclude
    exclude: [],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {},

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,

    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity
  })
}
