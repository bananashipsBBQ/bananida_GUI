SCRIPT_TEMPLATES = {
    'API_LOGGING': '''
Java.perform(function() {
    // Common Android API hooks
    var HttpURLConnection = Java.use('java.net.HttpURLConnection');
    var OkHttpClient = Java.use('okhttp3.OkHttpClient');
    var Retrofit = Java.use('retrofit2.Retrofit');
    
    // HTTP URL Connection
    HttpURLConnection.connect.implementation = function() {
        console.log('[+] HttpURLConnection.connect() called');
        console.log('URL: ' + this.getURL().toString());
        console.log('Method: ' + this.getRequestMethod());
        this.connect();
    };
    
    // OkHttp
    OkHttpClient.newCall.implementation = function(request) {
        console.log('[+] OkHttpClient.newCall() intercepted');
        console.log('URL: ' + request.url().toString());
        console.log('Method: ' + request.method());
        console.log('Headers: ' + request.headers().toString());
        return this.newCall(request);
    };
    
    // Retrofit
    Retrofit.create.implementation = function(service) {
        console.log('[+] Retrofit API Service created');
        console.log('Service: ' + service.toString());
        return this.create(service);
    };
});
''',

    'SSL_PINNING_BYPASS': '''
Java.perform(function() {
    var TrustManager = Java.registerClass({
        name: 'com.custom.TrustManager',
        implements: [Java.use('javax.net.ssl.X509TrustManager')],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    SSLContext.init.implementation = function(keyManager, trustManager, secureRandom) {
        console.log('[+] Bypassing SSL Pinning');
        var trustManagers = [TrustManager.$new()];
        this.init(keyManager, trustManagers, secureRandom);
    };
});
''',

    'APP_INFO': '''
Java.perform(function() {
    var ActivityThread = Java.use('android.app.ActivityThread');
    var Context = Java.use('android.content.Context');
    
    var currentApplication = ActivityThread.currentApplication();
    var context = currentApplication.getApplicationContext();
    
    console.log('\\n[App Information]');
    console.log('Package Name:', context.getPackageName());
    console.log('Process Name:', ActivityThread.currentProcessName());
    console.log('App Version:', context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName.value);
    console.log('Target SDK:', context.getApplicationInfo().targetSdkVersion.value);
    
    // List all activities
    var packageInfo = context.getPackageManager().getPackageInfo(context.getPackageName(), 
                     Java.use('android.content.pm.PackageManager').GET_ACTIVITIES.value);
    console.log('\\n[Activities]');
    packageInfo.activities.value.forEach(function(activity) {
        console.log(activity.name.value);
    });
});
''',

    'CUSTOM_API_LOGGER': '''
Java.perform(function() {
    // Add your custom API class/method hooks here
    var targetClass = Java.use('com.example.api.ServiceClass');
    
    targetClass.apiMethod.implementation = function() {
        console.log('[+] API Call Intercepted');
        console.log('Arguments:', arguments);
        var result = this.apiMethod.apply(this, arguments);
        console.log('Result:', result);
        return result;
    };
});
'''
} 