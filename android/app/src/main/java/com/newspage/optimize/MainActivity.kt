package com.newspage.optimize

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.ProcessLifecycleOwner
import com.newspage.optimize.data.SessionManager
import com.newspage.optimize.ui.theme.OptimizeTheme
import com.newspage.optimize.ui.navigation.AppNavigation

class MainActivity : ComponentActivity() {
    private var sessionManager: SessionManager? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            OptimizeTheme {
                AppNavigation(
                    onSessionExpired = {
                        // Navigate back to login when session expires
                        sessionManager?.reset()
                    }
                )
            }
        }

        // Set up session timeout (1 hour idle auto-logout)
        sessionManager = SessionManager(
            app = application,
            timeoutMs = 3_600_000L,
            onSessionExpired = {
                runOnUiThread {
                    // Session expired: recreate activity to go back to login
                    recreate()
                }
            },
        )
        ProcessLifecycleOwner.get().lifecycle.addObserver(sessionManager!!)
    }

    override fun onUserInteraction() {
        super.onUserInteraction()
        sessionManager?.onUserInteraction()
    }

    override fun onDestroy() {
        super.onDestroy()
        sessionManager?.let {
            ProcessLifecycleOwner.get().lifecycle.removeObserver(it)
            it.destroy()
        }
    }
}
