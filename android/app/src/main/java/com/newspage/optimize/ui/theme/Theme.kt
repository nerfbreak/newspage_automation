package com.newspage.optimize.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Brand colors from Streamlit design system
val BrandBlue = Color(0xFF0068C9)
val BrandDark = Color(0xFF31333F)
val BrandSurface = Color(0xFFF0F2F6)
val BrandError = Color(0xFFFF2B2B)
val BrandSuccess = Color(0xFF10B981)
val BrandTextMuted = Color(0xFF808495)
val BrandWhite = Color(0xFFFAFAFA)

private val LightColorScheme = lightColorScheme(
    primary = BrandBlue,
    onPrimary = Color.White,
    secondary = BrandDark,
    onSecondary = Color.White,
    background = Color.White,
    onBackground = BrandDark,
    surface = BrandSurface,
    onSurface = BrandDark,
    error = BrandError,
    onError = Color.White,
)

@Composable
fun OptimizeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        content = content,
    )
}
