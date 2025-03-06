package com.example.wasmjsruntime

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private lateinit var statusTextView: TextView
    private lateinit var startServiceButton: Button
    private lateinit var stopServiceButton: Button
    private lateinit var runJsButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusTextView = findViewById(R.id.statusTextView)
        startServiceButton = findViewById(R.id.startServiceButton)
        stopServiceButton = findViewById(R.id.stopServiceButton)
        runJsButton = findViewById(R.id.runJsButton)

        startServiceButton.setOnClickListener {
            startWasmRuntimeService()
            updateUI(true)
        }

        stopServiceButton.setOnClickListener {
            stopWasmRuntimeService()
            updateUI(false)
        }

        runJsButton.setOnClickListener {
            executeJavaScript()
        }
    }

    private fun startWasmRuntimeService() {
        val serviceIntent = Intent(this, WasmRuntimeService::class.java)
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun stopWasmRuntimeService() {
        val serviceIntent = Intent(this, WasmRuntimeService::class.java)
        stopService(serviceIntent)
    }

    private fun executeJavaScript() {
        val intent = Intent(WasmRuntimeService.ACTION_EXECUTE_JS)
        intent.putExtra(WasmRuntimeService.EXTRA_JS_CODE, "function add(a, b) { return a + b; }; add(40, 2);")
        sendBroadcast(intent)
    }

    private fun updateUI(isServiceRunning: Boolean) {
        startServiceButton.isEnabled = !isServiceRunning
        stopServiceButton.isEnabled = isServiceRunning
        runJsButton.isEnabled = isServiceRunning
        
        statusTextView.text = if (isServiceRunning) {
            "Service is running"
        } else {
            "Service is stopped"
        }
    }
}
