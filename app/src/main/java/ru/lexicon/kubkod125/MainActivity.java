package ru.lexicon.kubkod125;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity implements SensorEventListener {
    private WebView webView;
    private SensorManager sensorManager;
    private Sensor accelerometer;
    private long lastUpdate = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);

        // Поддержка телефонных звонков tel: из лаунчера КУБКОД
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (uri != null && "tel".equals(uri.getScheme())) {
                    Intent dialIntent = new Intent(Intent.ACTION_DIAL, uri);
                    startActivity(dialIntent);
                    return true;
                }
                return false;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);

        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (sensorManager != null) {
            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (sensorManager != null && accelerometer != null) {
            sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_GAME);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (sensorManager != null) {
            sensorManager.unregisterListener(this);
        }
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        long now = System.currentTimeMillis();
        if (now - lastUpdate < 65) return;
        lastUpdate = now;

        float ax = event.values[0];
        float ay = event.values[1];
        float az = event.values[2];

        final String js = String.format(java.util.Locale.US,
            "if(window.onHardwareAccel){ onHardwareAccel(%.4f, %.4f, %.4f); }",
            ax, ay, az);
        webView.post(() -> webView.evaluateJavascript(js, null));
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}
}
