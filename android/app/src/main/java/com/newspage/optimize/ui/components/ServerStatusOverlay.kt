package com.newspage.optimize.ui.components

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.newspage.optimize.data.ServerState
import com.newspage.optimize.data.ServerStatusManager
import com.newspage.optimize.ui.theme.BrandBlue

/**
 * Full-screen overlay shown during server cold start.
 * Displays "Waking server..." with elapsed time and a pulsing animation.
 */
@Composable
fun ServerStatusOverlay(
    serverState: ServerState,
    elapsedMs: Long,
    modifier: Modifier = Modifier,
) {
    if (serverState != ServerState.CHECKING && serverState != ServerState.WAKING) return

    // Pulsing animation
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = EaseInOutCubic),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "alpha",
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xCC000000)),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            CircularProgressIndicator(
                color = BrandBlue,
                modifier = Modifier.size(48.dp),
                strokeWidth = 3.dp,
            )

            Text(
                text = if (serverState == ServerState.CHECKING) "Connecting to server..."
                       else "Waking server...",
                color = Color.White,
                fontSize = 18.sp,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.animateContentSize(),
            )

            if (serverState == ServerState.WAKING) {
                Text(
                    text = "Cold start in progress (${elapsedMs / 1000}s)",
                    color = Color.White.copy(alpha = alpha),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                )

                Text(
                    text = "Render free tier servers sleep after 15 min of inactivity.\nThis usually takes 30-60 seconds.",
                    color = Color.White.copy(alpha = 0.6f),
                    fontSize = 11.sp,
                    lineHeight = 16.sp,
                    modifier = Modifier.padding(horizontal = 32.dp),
                )
            }
        }
    }
}
