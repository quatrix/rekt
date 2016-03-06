var gulp = require('gulp'),
    bundle = require('gulp-bundle-file'),
    gutil = require('gulp-util'),
    watch = require('gulp-watch'),
    jshint = require('gulp-jshint'),
    rimraf = require('gulp-rimraf'),
    uglify = require('gulp-uglify'),
    less = require('gulp-less'),
    runSequence = require('run-sequence'),
    angularFilesort = require('gulp-angular-filesort'),
    inject = require('gulp-inject'),
    livereload = require('gulp-livereload'),
    nodemon = require('gulp-nodemon'),
    print = require('gulp-print'),
    concat = require('gulp-concat'),
    minifyCSS = require('gulp-minify-css'),
    sourcemaps = require('gulp-sourcemaps'),
    changed = require('gulp-changed'),
    fs = require('fs'),
    _ = require('lodash');

var concatFiles = process.env.NODE_ENV === 'production'; //todo: determine/change based on target of compilation, and maybe add some more params, such as compression, maps etc.

var paths = {
    dist : 'server/public/',
    src: {
        client: 'client/',
        server: 'server/app/'
    }
};

var sources = {
    'bundle.js' : [paths.src.client + 'modules/**/*.js'],
    'bundle.css' : [paths.src.client + 'modules/**/module.less'],
    'bundle.css.watched' : [paths.src.client + 'modules/**/*.less'],
    'server.js' : [paths.src.server + '**/*.js', paths.src.server + '../server.js'],
    'statics' : ['**/*.html', '**/*.png', '**/*.gif', '**/*.ico', '**/images/**/*', '**/fonts/**/*.{ttf,woff,eof,svg}','!**/fonts/specimen_files'].map(function(f){return paths.src.client + f;}),
    'vendor.js.watched' : [paths.src.client + 'vendor.json'],
    'vendor.css.watched' : [paths.src.client + 'vendor.json'],
    get "vendor.js"(){
    var vendorSources = JSON.parse(fs.readFileSync('./client/vendor.json', 'utf-8'));
    return vendorSources.js.map(function (f) {
        return paths.src.client + f
    });
},
get "vendor.css"(){
    var vendorSources = JSON.parse(fs.readFileSync('./client/vendor.json', 'utf-8'));
    return vendorSources.css.map(function (f) {
        return paths.src.client + f
    });
}
};

gulp.task('clean-client', function (cb) {
    return gulp.src(paths.dist, {read: false})
        .pipe(rimraf());
});

gulp.task('server.js.lint', function () {
    return gulp.src(sources['server.js'])
        .pipe(jshint())
        .pipe(jshint.reporter(customJsHintErrorReporter));
});

gulp.task('bundle.js.lint', function () {
    return gulp.src(sources['bundle.js'])
        .pipe(jshint())
        .pipe(jshint.reporter(customJsHintErrorReporter));
});

gulp.task('all.js.lint', ['bundle.js.lint', 'server.js.lint']);

gulp.task('server.js', ['server.js.lint'], function (cb) {
    cb();
});

gulp.task('statics', function(){
    return gulp.src(sources['statics'])
        .pipe(changed(paths.dist))
        .pipe(gulp.dest(paths.dist));
});

gulp.task('bundle.css', function(){

    if(concatFiles) {
        return gulp.src(sources['bundle.css'])
            .pipe(sourcemaps.init())
            .pipe(less())
            .pipe(sourcemaps.write())
            //.pipe(print())
            .pipe(sourcemaps.init({loadMaps: true}))
            .pipe(concat('bundle.css'))
            .pipe(sourcemaps.write())
            .pipe(gulp.dest(paths.dist));
    }

    return gulp.src(sources['bundle.css'])
        .pipe(less())
        .pipe(bundle('bundle.css', {type: 'css', base: paths.src.client}))
        //.pipe(changed(paths.dist))
        .pipe(gulp.dest(paths.dist));
});

gulp.task('vendor.js', function() {
    return bundleJs(
        gulp.src(sources['vendor.js']),
        'vendor.js'
    );
});

gulp.task('bundle.js', ['bundle.js.lint'], function() {
    //console.log(this);
    return bundleJs(
        gulp.src(sources['bundle.js'])
            .pipe(angularFilesort())
            .on('error', function(err){gutil.log(err); this.emit('end');}),
        'bundle.js'
    );
});




gulp.task('vendor.css', function() {

    if(concatFiles){
        return gulp.src(sources['vendor.css'])
            .pipe(sourcemaps.init())
            .pipe(minifyCSS({keepBreaks:true, root: 'client/'}))
            .pipe(sourcemaps.write())
            .pipe(sourcemaps.init({loadMaps: true}))
            .pipe(concat('vendor.css'))
            .pipe(sourcemaps.write())
            .pipe(gulp.dest(paths.dist));
    }

    return gulp.src(sources['vendor.css'])
        .pipe(minifyCSS({keepBreaks:true}))
        .pipe(bundle('vendor.css', {type: 'css', base: paths.src.client}))
        .pipe(changed(paths.dist))
        .pipe(gulp.dest(paths.dist));

});


gulp.task('watch', function(){

    _.each(sources, function(v,k){
        if(/\.watched$/.test(k)){
            return;
        }
        v = sources[k+'.watched'] || v;
        watch({glob: v, emitOnGlob: false}, [k]);
    });

    //watch({glob: [paths.src.client + 'vendor.json']}, ['vendor.js']); todo: need to also reload the json!

    livereload.listen();

    watch({glob: 'server/public/**/*.*', emitOnGlob: false}, function(files){
        files.pipe(livereload());
    });


});

gulp.task('serve', function () {

    var nodeArgs = process.env.NODEMON_NODEARGS && process.env.NODEMON_NODEARGS.split(';');

    nodemon({
        script: './server/server.js',
        watch: ['./server/'],
        ext: 'html js',
        nodeArgs: nodeArgs || undefined,
        ignore: ['./server/public']
    })
        //.on('change', ['server-lint'])
        .on('restart', function () {

            gutil.log('restarted!');
        })
});

gulp.task('build-client', ['bundle.js', 'vendor.js', 'vendor.css', 'bundle.css', 'statics']);


gulp.task('rebuild-client', function(cb){
    runSequence('clean-client', 'build-client', cb);
});

gulp.task('rebuild-and-watch', ['rebuild-client'], function(){
    gulp.start('watch');

});

gulp.task('default', ['rebuild-and-watch'],function(){
    return gulp.start('serve');
});

// call when developing gulp itself: gulp auto-reload [--task taskName]
gulp.task('auto-reload', function() {
    var argv = require('yargs').argv,
        spawn = require('child_process').spawn,
        p;

    gulp.watch('gulpfile.js', spawnChildren);
    spawnChildren();

    function spawnChildren(e) {
        // kill previous spawned process
        if(p) { p.kill(); }

        // `spawn` a child `gulp` process linked to the parent `stdio`
        p = spawn('gulp', [argv.task||'default'], {stdio: 'inherit'});

        //gutil.log(p.pid);
    }
});

// hacks and helper functions
function bundleJs(srcStream, outputFile){

    if(concatFiles){
        return srcStream.pipe(sourcemaps.init())
            //.pipe(print())
            .pipe(concat(outputFile))
            .pipe(uglify())
            .pipe(sourcemaps.write())
            .pipe(gulp.dest(paths.dist));
    }

    return srcStream
        .pipe(bundle(outputFile, {base: paths.src.client}))
        .pipe(changed(paths.dist))
        .pipe(gulp.dest(paths.dist));
}


function customJsHintErrorReporter(errors) {
    var path = require('path'),
        tpl = _.template('${error.code} - ${basename}:${error.line}:${error.character} ${error.reason} ${error.evidence}');
    _.each(errors, function(e){
        e.evidence = (e.evidence || '').trim();
        e.basename = e.file.replace(/^.*\/modules\//, '');
        gutil.log(gutil.colors.red('jshint: ' + tpl(e)));
    });
}





