package ru.lexicon.kubkod125;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.ContactsContract;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity implements SensorEventListener {
    private WebView webView;
    private SensorManager sensorManager;
    private Sensor accelerometer;
    private long lastUpdate = 0;

    private static final int REQ_FILE_CHOOSER = 1001;
    private static final int REQ_PICK_CONTACT = 1002;
    private ValueCallback<Uri[]> filePathCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        // Прямой мост Java <-> КУБКОД для системного выбора контактов
        webView.addJavascriptInterface(new KubkodBridge(), "AndroidBridge");

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

        // Включаем поддержку открытия системного проводника для выбора файла .VCF
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (MainActivity.this.filePathCallback != null) {
                    MainActivity.this.filePathCallback.onReceiveValue(null);
                }
                MainActivity.this.filePathCallback = filePathCallback;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                startActivityForResult(Intent.createChooser(intent, "Выберите файл контактов .VCF"), REQ_FILE_CHOOSER);
                return true;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);

        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (sensorManager != null) {
            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        }
    }

    public class KubkodBridge {
        @JavascriptInterface
        public void pickSystemContact() {
            Intent intent = new Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI);
            startActivityForResult(intent, REQ_PICK_CONTACT);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE_CHOOSER) {
            if (filePathCallback == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK && data != null && data.getData() != null) {
                results = new Uri[]{ data.getData() };
            }
            filePathCallback.onReceiveValue(results);
            filePathCallback = null;
        } else if (requestCode == REQ_PICK_CONTACT) {
            if (resultCode == Activity.RESULT_OK && data != null && data.getData() != null) {
                Uri contactUri = data.getData();
                String[] projection = new String[]{
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                    ContactsContract.CommonDataKinds.Phone.NUMBER
                };
                try (Cursor cursor = getContentResolver().query(contactUri, projection, null, null, null)) {
                    if (cursor != null && cursor.moveToFirst()) {
                        String name = cursor.getString(0);
                        String number = cursor.getString(1);
                        if (name == null) name = "Контакт";
                        if (number == null) number = "";
                        final String safeName = name.replace("'", "\'").replace("
", " ");
                        final String safeNum = number.replace("'", "\'").replace("
", " ");
                        webView.post(() -> webView.evaluateJavascript(
                            "if(window.onNativeContactPicked){ onNativeContactPicked('" + safeName + "', '" + safeNum + "'); }", null));
                    }
                } catch (Exception ignored) {}
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
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
