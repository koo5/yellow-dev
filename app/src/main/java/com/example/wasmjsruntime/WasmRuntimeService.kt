package com.example.wasmjsruntime

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.bytecodealliance.wasmtime.Engine
import org.bytecodealliance.wasmtime.Module
import org.bytecodealliance.wasmtime.Store
import org.bytecodealliance.wasmtime.Func
import org.bytecodealliance.wasmtime.Instance
import org.bytecodealliance.wasmtime.Linker
import org.bytecodealliance.wasmtime.WasmFunctions
import org.bytecodealliance.wasmtime.WasmValType
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class WasmRuntimeService : Service() {
    companion object {
        private const val TAG = "WasmRuntimeService"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "WasmRuntimeChannel"
        
        const val ACTION_EXECUTE_JS = "com.example.wasmjsruntime.EXECUTE_JS"
        const val EXTRA_JS_CODE = "js_code"
    }

    private val serviceJob = SupervisorJob()
    private val serviceScope = CoroutineScope(Dispatchers.IO + serviceJob)
    
    private var wasmEngine: Engine? = null
    private var wasmStore: Store<Void>? = null
    private var quickJsModule: Module? = null
    private var quickJsInstance: Instance? = null
    
    private val jsExecutionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == ACTION_EXECUTE_JS) {
                val jsCode = intent.getStringExtra(EXTRA_JS_CODE) ?: return
                executeJavaScript(jsCode)
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        registerReceiver(jsExecutionReceiver, IntentFilter(ACTION_EXECUTE_JS), RECEIVER_EXPORTED)
        
        serviceScope.launch {
            initializeWasmRuntime()
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        unregisterReceiver(jsExecutionReceiver)
        serviceJob.cancel()
        cleanupWasmRuntime()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Wasm Runtime Service"
            val descriptionText = "Running JavaScript in WebAssembly"
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Wasm Runtime Service")
            .setContentText("Running JavaScript in WebAssembly")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentIntent(pendingIntent)
            .build()
    }

    private fun initializeWasmRuntime() {
        try {
            // Extract QuickJS WebAssembly binary from assets
            val quickJsWasmBytes = extractWasmBinary("quickjs.wasm")
            
            // Initialize Wasmtime
            wasmEngine = Engine()
            wasmStore = Store.withoutData(wasmEngine)
            
            // Load QuickJS module
            quickJsModule = Module.fromBinary(wasmEngine, quickJsWasmBytes)
            
            // Create linker and define imports
            val linker = Linker(wasmEngine)
            
            // Define host functions that QuickJS might need
            defineHostFunctions(linker)
            
            // Instantiate the module
            quickJsInstance = linker.instantiate(wasmStore, quickJsModule)
            
            Log.d(TAG, "Wasm runtime initialized successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize Wasm runtime", e)
        }
    }

    private fun defineHostFunctions(linker: Linker) {
        // Define print function
        val printFunc = Func.wrap(
            wasmStore,
            { ptr: Int, len: Int ->
                // This would read a string from WebAssembly memory and print it
                Log.d(TAG, "QuickJS print: Memory[$ptr:$len]")
            },
            WasmValType.I32, WasmValType.I32
        )
        
        linker.define("env", "js_print", printFunc)
        
        // Add more host functions as needed
    }

    private fun executeJavaScript(jsCode: String) {
        serviceScope.launch {
            try {
                val instance = quickJsInstance ?: throw IllegalStateException("QuickJS not initialized")
                val store = wasmStore ?: throw IllegalStateException("Wasm store not initialized")
                
                // Get the eval function from the instance
                val evalFunc = instance.getFunc(store, "js_eval").get()
                
                // Convert JS code to bytes and pass to the eval function
                // This is a simplified example - actual implementation would need to handle memory allocation
                val result = WasmFunctions.consumer(store, evalFunc).accept(jsCode)
                
                Log.d(TAG, "JavaScript execution result: $result")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to execute JavaScript", e)
            }
        }
    }

    private fun extractWasmBinary(assetName: String): ByteArray {
        try {
            // First check if we already extracted it
            val file = File(filesDir, assetName)
            if (file.exists()) {
                return file.readBytes()
            }

            // Extract from assets
            assets.open(assetName).use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }
            
            return file.readBytes()
        } catch (e: IOException) {
            Log.e(TAG, "Failed to extract WASM binary", e)
            throw e
        }
    }

    private fun cleanupWasmRuntime() {
        quickJsInstance = null
        quickJsModule = null
        wasmStore = null
        wasmEngine = null
    }
}
