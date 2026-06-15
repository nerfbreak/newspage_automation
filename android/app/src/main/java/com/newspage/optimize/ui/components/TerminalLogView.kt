package com.newspage.optimize.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.newspage.optimize.data.WSMessage
import com.newspage.optimize.ui.theme.BrandBlue
import com.newspage.optimize.ui.theme.BrandSuccess
import com.newspage.optimize.ui.theme.BrandError
import com.newspage.optimize.ui.theme.BrandTextMuted

/**
 * Terminal-style log view with color-coded module tags and auto-scroll.
 * Matches the Streamlit terminal-box styling.
 */
@Composable
fun TerminalLogView(
    messages: List<WSMessage>,
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()

    // Auto-scroll to bottom
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFF1E1E2E), RoundedCornerShape(8.dp))
            .padding(12.dp)
    ) {
        LazyColumn(state = listState) {
            items(messages) { msg ->
                if (msg.type == "log") {
                    val tagColor = when (msg.module.uppercase()) {
                        "AUTH" -> Color(0xFF89B4FA)
                        "NAV" -> Color(0xFFF9E2AF)
                        "INJECT" -> Color(0xFFCBA6F7)
                        "SERVER" -> Color(0xFFA6E3A1)
                        "SUCCESS" -> BrandSuccess
                        "ERROR", "WARN" -> BrandError
                        "SYS" -> BrandTextMuted
                        else -> Color.White
                    }

                    Text(
                        buildAnnotatedString {
                            withStyle(SpanStyle(color = Color(0xFF6C7086), fontSize = 11.sp)) {
                                append("[${msg.timestamp}]")
                            }
                            withStyle(SpanStyle(color = Color(0xFF585B70), fontSize = 11.sp)) {
                                append("[+${msg.elapsedMs}ms]")
                            }
                            withStyle(SpanStyle(color = tagColor, fontSize = 11.sp)) {
                                append("[${msg.module}]")
                            }
                            withStyle(SpanStyle(color = Color(0xFFCDD6F4), fontSize = 11.sp)) {
                                append(" ${msg.msg}")
                            }
                        },
                        fontSize = 11.sp,
                        modifier = Modifier.padding(vertical = 1.dp),
                    )
                }
            }

            // Blinking cursor
            item {
                Text(
                    text = "\u2588",
                    color = Color(0xFFCDD6F4),
                    fontSize = 11.sp,
                )
            }
        }
    }
}
