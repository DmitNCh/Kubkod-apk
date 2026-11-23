package ru.lexicon.kubkod125;

import android.app.Activity;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;

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
        if (now - lastUpdate < 80) return;
        lastUpdate = now;

        float ax = event.values[0];
        float ay = event.values[1];
        float az = event.values[2];
        double mag = Math.sqrt(ax * ax + ay * ay + az * az);
        double dyn = Math.abs(mag - 9.81);
        double clean = Math.tanh(dyn * 0.25);
        double noisy = Math.tanh((ax - ay + az) * 0.15);

        final String js = String.format(java.util.Locale.US,
            "if(window.stepKubkod && sensorActive){ document.getElementById('accelVal').textContent='%.2f м/с²'; stepKubkod(%.5f, %.5f); }",
            dyn, clean, noisy);
        webView.post(() -> webView.evaluateJavascript(js, null));
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}
}
